import sys
import glob
import re
import subprocess

from drizzlepac.hlautils.astroquery_utils import retrieve_observation

from crds.bestrefs import bestrefs

import boto3

from . import log

# -----------------------------------------------------------------------------

IPPPSSOOT_RE = re.compile(r"^[IJLO][A-Z0-9]{8,8}$")

IPPPSSOOT_INSTR = {
    "J" : "acs",
    "U" : "wfpc2",
    "V" : "hsp",
    "W" : "wfpc",
    "X" : "foc",
    "Y" : "fos",
    "Z" : "hrs",
    "E" : "eng",
    "F" : "fgs",
    "I" : "wfc3",
    "N" : "nicmos",
    "O" : "stis",
    "L" : "cos",
}

INSTRUMENTS = set(IPPPSSOOT_INSTR.values())

def get_instrument(ipppssoot):
    """Given an IPPPSSOOT ID, return the corresponding instrument.
    """
    if ipppssoot.lower() in INSTRUMENTS:
        return ipppssoot.lower()
    else:
        return IPPPSSOOT_INSTR.get(ipppssoot.upper()[0])

# -----------------------------------------------------------------------------

def get_output_path(bucket, prefix, ipppssoot):
    """
    >>> get_output_path("s3://temp", "none", "IC0B02020")
    's3://temp/wfc3/IC0B02020'

    >>> get_output_path("s3://temp", "batch-2020-02-13T10:33:00/IC0B02020", "IC0B02020")
    's3://temp/batch-2020-02-13T10:33:00/wfc3/IC0B02020'

    >>> get_output_path("s3://temp", "batch-2020-02-13T10:33:00", "IC0B02020")
    's3://temp/batch-2020-02-13T10:33:00/wfc3'
    """
    instrument_name = get_instrument(ipppssoot)
    if prefix in [None, "none"]:
        prefix = instrument_name + "/" + ipppssoot
    else:
        if re.match(IPPPSSOOT_RE, prefix.split("/")[-1]):
            # Only use prefix IPPPSSOOT to indicate desire for ipppsoot
            # Use actual IPPPSSOOT to support multi-ipppssoot jobs with
            # individualized output directories.

            # remove ipppsssoot
            prefix = "/".join(prefix.split("/")[:-1])

            # Add back instrument + ipppssoot
            prefix = prefix + "/" + instrument_name + "/" + ipppssoot
        else:
            prefix = prefix + "/" + instrument_name
    return bucket + "/" + prefix

# -------------------------------------------------------------

def upload_filename(filename, s3_filepath):
    client = boto3.client('s3')
    if s3_filepath.startswith("s3://"):
        s3_filepath = s3_filepath[5:]
    bucket = s3_filepath.split("/")[0]
    objectname = "/".join(s3_filepath.split("/")[1:])
    with open(filename, "rb") as f:
        client.upload_fileobj(f, bucket, objectname)

# -----------------------------------------------------------------------------

class InstrumentManager:
    instrument_name = None     # abstract class
    download_suffixes = None
    not_so_bad_err_nums = []

    def __init__(self, ipppssoot):
        self.ipppssoot = ipppssoot

    # .............................................................

    def raw_files(self, files):
        return [f for f in files if "_raw" in f]

    def assoc_files(self, files):
        return [f for f in files if f.endswith("_asn.fits")]

    def unassoc_files(self, files):  # can be overriden by subclasses
        return self.raw_files(files)

    # def bestrefs_files(self, files):
    #     assoc = self.assoc_files(files)
    #     if assoc:
    #         return assoc
    #     else:
    #         return self.unassoc_files(files)

    # .............................................................

    def divider(self, *args, dash=">"):
        msg = " ".join([str(a) for a in args])
        dashes = (100-len(msg)-2-5)
        log.info(dash *(5 + len(msg) + dashes + 2))
        log.info(dash*5, msg, dash*dashes)

    def run(self, cmd, *args):
        cmd = tuple(cmd.split()) + args  # Handle stage values with switches.
        self.divider("Running:", cmd)
        err = subprocess.call(cmd)
        if err in self.not_so_bad_err_nums:
            log.info("Skipping 'not so bad' error status =", err)
            err = 0
        if err:
            log.error(self.ipppssoot, "Command:", repr(cmd), "exited with error status:", err)
            sys.exit(1)     # should be 0-127,  higher err val's like 512 are truncated to 0 by shells

    # .............................................................

    def dowload(self):
        self.divider("Retrieving data files for:", self.download_suffixes)
        files = retrieve_observation(self.ipppssoot, suffix=self.download_suffixes)
        self.divider("Download data complete.")
        return list(sorted(files))

    def assign_bestrefs(self, files):
        self.divider("Computing bestrefs and downloading references.", files)
        bestrefs_files = self.raw_files(files)
        # bestrefs_files = self.bestrefs_files(files)
        # if not bestrefs_files:
        #     self.divider("Bestrefs: no applicable data files, skipping...", files)
        #     return []
        bestrefs.assign_bestrefs(bestrefs_files, sync_references=True)
        self.divider("Bestrefs complete.")
        return bestrefs_files

    def process(self, files):
        assoc = self.assoc_files(files)
        if assoc:
            self.run(self.stage1, *assoc)
            if self.stage2:
                self.run(self.stage2, *assoc)
            return
        unassoc = self.unassoc_files(files)
        if unassoc:
            self.run(self.stage1, *unassoc)
            return

    def output_files(self, bucket=None, prefix=None):
        # include all fits files,  including modified inputs.
        outputs = glob.glob("*.fits")
        outputs += glob.glob("*.tra")
        self.divider("Saving outputs:", bucket, prefix, outputs)
        output_path = get_output_path(bucket, prefix, self.ipppssoot)
        paths = []
        for filename in outputs:
            s3_filepath = output_path + "/" + filename
            log.info("Saving:", s3_filepath)
            upload_filename(filename, s3_filepath)
            paths.append(s3_filepath)
        return paths

    # .............................................................

    def main(self, ipppssoot, output_bucket, prefix):
        """Perform all processing steps for basic calibration processing:

        download inputs
        assign bestrefs (and potentially download refs)
        perform CAL processing
        copy outputs to S3

        Returns [ output_files, ... ]
        """
        input_files = self.dowload()

        self.assign_bestrefs(input_files)

        self.process(input_files)

        outputs = self.output_files(output_bucket, prefix)

        return outputs

# -----------------------------------------------------------------------------

class AcsManager(InstrumentManager):
    instrument_name = "acs"
    download_suffixes = ["ASN", "RAW"]
    stage1 = "calacs.e"
    stage2 = "runastrodriz"

class Wfc3Manager(InstrumentManager):
    instrument_name = "wfc3"
    download_suffixes = ["ASN", "RAW"]
    stage1 = "calwf3.e"
    stage2 = "runastrodriz"

# ............................................................................

class CosManager(InstrumentManager):
    instrument_name = "cos"
    download_suffixes = ["ASN", "RAW", "EPC", "RAWACCUM", "RAWACCUM_A", "RAWACCUM_B", "RAWACQ", "RAWTAG", "RAWTAG_A", "RAWTAG_B"]
    stage1 = "calcos"
    stage2 = None
    not_so_bad_err_nums = [
        5,    # Ignore calcos errors from RAWACQ
    ]

    def unassoc_files(self, files):
        return super(CosManager, self).raw_files(files)[:1]   # return only first file

# ............................................................................

class StisManager(InstrumentManager):
    instrument_name = "stis"
    download_suffixes = ["ASN", "RAW", "EPC", "TAG", "WAV"]
    stage1 = "cs0.e -tv"
    stage2 = None

    def process(self, files):
        raw = [ f for f in files if f.endswith("_raw.fits")]
        wav = [ f for f in files if f.endswith("_wav.fits")]
        if raw:
            self.run(self.stage1, *raw)
        else:
            self.run(self.stage1, *wav)

    def raw_files(self, files):
        return [f for f in files if f.endswith(('_raw.fits','_wav.fits','_tag.fits'))]

# ............................................................................

MANAGERS = {
    "acs" : AcsManager,
    "cos" : CosManager,
    "stis" : StisManager,
    "wfc3" : Wfc3Manager,
}

def get_instrument_manager(ipppssoot):
    instrument = get_instrument(ipppssoot)
    manager = MANAGERS[instrument](ipppssoot)
    manager.divider("Started processing for", instrument)
    return manager

# -----------------------------------------------------------------------------

def process(ipppssoot, output_bucket=None, prefix=None):
    """Given a `prefix` a dataset `ipppssoot` ID and an S3 `output_bucket`,
    process the dataset and upload output products to the `output_bucket` with
    the given `prefix`.

    Nominally `prefix` identifies a job or batch of files dumped into an
    otherwise immense bucket.
    """
    manager = get_instrument_manager(ipppssoot)

    outputs = manager.main(ipppssoot, output_bucket, prefix)

    return outputs

# -----------------------------------------------------------------------------

def process_ipppssoots(ipppssoots, output_bucket=None, prefix=None):
    for ipppssoot in ipppssoots:
        process(ipppssoot, output_bucket, prefix)

# -----------------------------------------------------------------------------

def test():
    from hstdputils import process
    import doctest
    return doctest.testmod(process)

if __name__ == "__main__":
    output_bucket = sys.argv[1]
    prefix = sys.argv[2]
    ipppssoots = sys.argv[3:]
    if output_bucket.lower() == "none":
        output_bucket = None
    if prefix.lower() == "none":
        prefix = None
    process_ipppssoots(ipppssoots, output_bucket, prefix)
