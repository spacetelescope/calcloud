"""This module handles syncing calcloud processing outputs
from S3 to a local file system,  nominally downloading from
AWS to STScI's archive ingest.
"""
import os
import argparse
import time
import glob
import shutil
import json
import traceback

import yaml

from calcloud import s3
from calcloud import timing
from calcloud import log
from calcloud import hst


# ----------------------------------------------------------------------

MAX_DATASETS_PER_BATCH = 10**6

# ----------------------------------------------------------------------


class FsMessenger:
    """This class implements Messenger methods needed to output
    messages to a file system,  nominally for communicating about
    datasets which are ready to archive.
    """
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def data_path(self, dataset_subpath):
        return os.path.join(self.output_dir, "data", dataset_subpath)

    def message_path(self, kind, dataset):
        """Return the path to the message file of type `kind`
        named `dataset`.
        """
        return os.path.join(self.output_dir, "messages", kind, dataset[0])

    def message_name(self, message_path):
        return os.path.basename(message_path)

    def send(self, kind, dataset, text=""):
        """Send message of type `kind` with name `dataset`
        and contents `text` which defaults to the empty string.
        """
        msg_path = self.message_path(kind, dataset)
        os.makedirs(os.path.dirname(msg_path), exist_ok=True)
        with open(msg_path, "w+") as msg:
            msg.write(text)

    def pass_message(self, old_kind, new_kind, dataset):
        """Given the `dataset` with (dataset_name, _),  move the message
        from type `old_kind` to type `new_kind`.
        """
        old_path = self.message_path(old_kind, dataset)
        new_path = self.message_path(new_kind, dataset)
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.move(old_path, new_path)

    def reset(self, kinds):
        """Delete all messages of types in list `kinds`."""
        for kind in kinds:
            where = self.message_path(kind, "*")
            log.info(f"Removing messages at '{where}'")
            msgs = glob.glob(where)
            for msg in msgs:
                os.remove(msg)

# ----------------------------------------------------------------------

class Syncer:
    """The Syncer class polls for batches of reprocessing outputs at
    `s3_output_path` and downloads them to appropriate batch sub-directories
    of `output_dir`.

    The Syncer is structured with a double loop over batches and datasets
    within each batch.

    The Syncer checks S3 for new batches or newly available datasets every
    `poll_seconds`.   (Messages are passed between the reprocessing system
    and Syncer via S3 objects and move lineraly through different processing
    states as-if being passed from one queue to the next.)
    """
    def __init__(self, s3_output_path, output_dir, poll_seconds=60):
        self._s3_output_path = s3_output_path
        self._output_dir = output_dir
        self._poll_seconds = poll_seconds
        self.s3_bmsgs = s3.S3Messenger(s3_output_path)   # batch level
        self.s3_dmsgs = None                             # dataset level
        self.fs_dmsgs = None                             # dataset level
        self.stats = timing.TimingStats()

    def main(self):
        """Forever,  watch for new batches.   When a new batch is found,
        archive every dataset found in the batch.    Exit via Control-c.
        """
        try:
            while True:
                self._check_and_process_batch()
        except KeyboardInterrupt:
            log.info("Control-c received, exiting...")
        log.standard_status()

    def _check_and_process_batch(self):
        """Receive one batch message and handle throttling and message passing,
        calling core method _archive_batch() to do the real work of archiving a batch.
        The batch message nominally moves from batch-new to batch-syncing to batch-done.
        If an error occurs it is moved to batch-error.
        """
        batch = self.s3_bmsgs.receive_and_resend("batch-new", "batch-syncing")
        if batch:
            try:
                self._archive_batch(batch)
                self.s3_bmsgs.pass_message("batch-syncing", "batch-done", batch)
            except Exception:
                batch = self._handle_exception("Batch", batch)
                self.s3_bmsgs.pass_message("batch-syncing", "batch-error", batch)
            finally:
                self.stats.report_stats()
        self.throttle(bool(batch))

    def _batch_complete(self, all_datasets):
        """Given a list of `all_datasets` names,  check to see if every dataset
        in the list is in one of the dataset final states: error or synced.
        """
        log.info("Checking for batch completion.")
        n_datasets = len(all_datasets)
        archived = self.s3_dmsgs.list_names("dataset-synced", max_messages=MAX_DATASETS_PER_BATCH)
        error = self.s3_dmsgs.list_names("dataset-error", max_messages=MAX_DATASETS_PER_BATCH)
        log.info(f"Archived={len(archived)} Error={len(error)} ExpectedTotal={n_datasets}.")
        datasets_s3 = set(archived + error)
        if all_datasets == datasets_s3:
            log.info("Batch complete.")
            return True
        log.info("Batch continuing...")
        return False

    def _archive_batch(self, batch):
        """Given a `batch` message defining the (name, contents) of the batch
        description file,  process every dataset in that batch.
        """
        self.stats.start()
        all_datasets = self._setup_batch(batch)
        while not self._batch_complete(all_datasets):
            synced_something = self._process_one_dataset()
            self.throttle(synced_something)

    def _process_one_dataset(self):
        """Pull one dataset from the 'dataset-processed' queue and archive it.

        Address messaging and error handling in this function propagating the
        dataset messge through states: dataset-processed, -syncing, -synced, -archived,
        and/or -error.

        Call the core sync(), archive(), and  archive_complete() to handle the
        real work of downloading the data and ingesting it into the archive.
        """
        dataset = self.s3_dmsgs.receive_and_resend("dataset-processed", "dataset-syncing")
        if not dataset:
            return False
        try:
            downloads = self.sync(dataset)
        except Exception:
            dataset = self._handle_exception("Syncing", dataset)
            self.s3_dmsgs.pass_message("dataset-syncing", "dataset-error", dataset)
            return False
        self.s3_dmsgs.pass_message("dataset-syncing", "dataset-synced", dataset)
        self.fs_dmsgs.send("dataset-synced", dataset, "\n".join(downloads)+"\n")
        # try:
        #     self.archive(dataset, downloads)
        # except Exception:
        #     dataset = self._handle_exception("Archiving", dataset)
        #     self.s3_dmsgs.pass_message("dataset-synced", "dataset-error", dataset)
        #     self.fs_dmsgs.pass_message("dataset-synced", "dataset-error", dataset)
        #     return False
        # self.s3_dmsgs.pass_message("dataset-synced", "dataset-archived", dataset)
        # self.fs_dmsgs.pass_message("dataset-synced", "dataset-archived", dataset)
        # return True

    def _setup_batch(self, batch):
        """Load the contents of S3 message `batch` as either YAML or JSON depending
        on the extension on the message's name.   Extract the dataset names of the
        batch from the contents.

        Using an extension-less batch_name derived from the name in `batch`,  create
        an input batch dataset S3 messenger and an output batch dataset file system
        messenger.

        Returns [all datasets to archive in batch]
        """
        batch_name, batch_contents = batch
        if batch_name.endswith(".yaml"):
            batch_info = yaml.safe_load(batch_contents)
        elif batch_name.endswith(".json"):
            batch_info = json.loads(batch_contents)
        else:
            raise ValueError("Unknown file type for batch: " +  repr(batch_name))
        batch_name = batch_name.split(".")[0]  # drop extension
        all_datasets = set(dataset_name.lower() for dataset_name in batch_info["datasets"])
        log.info(f"Starting sync for '{batch_name}' with {len(all_datasets)} datasets.")
        self.s3_dmsgs = s3.S3Messenger(self.s3_bmsgs.data_path(batch_name))
        self.fs_dmsgs = FsMessenger(os.path.join(self._output_dir, batch_name))
        return all_datasets

    def _handle_exception(self, activity, message):
        """Do common functions related to exception handling for an action
        named `activity` operating on S3 `message` of (name, contents).
        """
        exc = traceback.format_exc()
        log.error(f"{activity} {message[0]} failed with:\n{exc}.")
        message_name, contents = message
        contents += "# " + "="*40 + "\n" + exc
        return (message_name, contents)

    def sync(self, dataset):
        """Download the files associated with S3 message `dataset` of
        (dataset_name, empty_contents) to the path defined for `dataset_name`
        by the dataset file system messenger.  Output a file system message
        with type 'dataset-synced' containing the absolute local paths of
        downloaded files.

        Return [Absolute filepaths of downloaded files]
        """
        dataset_name, _contents = dataset
        instrument = hst.get_instrument(dataset_name)
        s3_path = self.s3_dmsgs.data_path(instrument + "/" + dataset_name) # data dir path
        local_path = self.fs_dmsgs.data_path(instrument + "/" + dataset_name) # data dir path
        downloads = self.s3_dmsgs.download_directory(local_path, s3_path)
        self._track_stats(dataset_name, downloads)
        return downloads

    # def archive(self, dataset, downloads):
    #     """Archive the outputs associated with S3 message `dataset` of
    #     (dataset_name, empty_contents) and/or the list of absolute local
    #     file system paths specified by `downloads`.
    #     """
    #     dataset_name, _contents = dataset
    #     instrument = hst.get_instrument(dataset_name)
    #     dataset_path = self.fs_dmsgs.data_path(instrument + "/" + dataset_name)
    #     log.info(f"Archiving dataset: '{dataset_path}'.")

    def _track_stats(self, dataset, downloads):
        n_bytes = timing.total_size(downloads)
        log.info(f"Downloaded {len(downloads)} files for '{dataset}' "
                 f"totalling {timing.human_format_number(n_bytes)}.")
        self.stats.increment("datasets")
        self.stats.increment("files", len(downloads))
        self.stats.increment("bytes", n_bytes)
        self.stats.report_stats()

    def throttle(self, had_messages):
        if had_messages:
            time.sleep(5)
        else:
            log.verbose(f"Sleeping for {self._poll_seconds} seconds...")
            time.sleep(self._poll_seconds)

    def reset(self):
        self.s3_bmsgs.reset("batch-new", ["batch-syncing", "batch-done", "batch-error"])
        for batch in self.s3_bmsgs.list_names("batch-new"):
            batch_name = batch.split(".")[0]
            self.s3_dmsgs = s3.S3Messenger(self.s3_bmsgs.data_path(batch_name))
            self.fs_dmsgs = FsMessenger(os.path.join(self._output_dir, batch_name))
            self.s3_dmsgs.reset("dataset-processed",
                ["dataset-syncing", "dataset-synced", "dataset-archived", "dataset-error"])
            self.fs_dmsgs.reset(["dataset-synced", "dataset-archived", "dataset-error"])

# ----------------------------------------------------------------------


def main(args=None):
    parser = argparse.ArgumentParser(
        description='Sync files from AWS S3 paths to the local file system.')
    parser.add_argument('--s3-output-path', dest='s3_output_path',
        help='AWS S3 batch output directory to be synced.')
    parser.add_argument('--output-dir', dest='output_dir',
        help='Root destination directory for all data subdirectories in a batch.')
    parser.add_argument(
        '--poll-seconds', dest='poll_seconds', type=float, default=60,
        help='Period at which to check for S3 messages.')
    parser.add_argument(
        '--verbose', dest="verbose", action="store_true",
        help='Issue debug level log messages.')
    parser.add_argument(
        '--reset', dest='reset', action='store_true',
        help='Move all messages in s3_outputs to their initial states.')
    parsed = parser.parse_args(args)
    if parsed.verbose:
        log.set_verbose()
    syncer = Syncer(
        s3_output_path=parsed.s3_output_path,
        output_dir=parsed.output_dir,
        poll_seconds=parsed.poll_seconds)
    if parsed.reset:
        syncer.reset()
    else:
        syncer.main()


if __name__ == "__main__":
    main()
