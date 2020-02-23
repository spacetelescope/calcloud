import sys
import glob
import re
import subprocess

# -----------------------------------------------------------------------------

from drizzlepac.hlautils.astroquery_utils import retrieve_observation

from crds.bestrefs import bestrefs

import boto3

from . import log

# -----------------------------------------------------------------------------

IPPPSSOOT_RE = re.compile(r"^[IJLO][A-Z0-9]{8,8}$")

# Note: only ACS, COS, STIS, and WFC3 are initially supported
IPPPSSOOT_INSTR = {
    "J": "acs",
    "U": "wfpc2",
    "V": "hsp",
    "W": "wfpc",
    "X": "foc",
    "Y": "fos",
    "Z": "hrs",
    "E": "eng",
    "F": "fgs",
    "I": "wfc3",
    "N": "nicmos",
    "O": "stis",
    "L": "cos",
}

INSTRUMENTS = set(IPPPSSOOT_INSTR.values())


def get_instrument(ipppssoot):
    """Given an IPPPSSOOT ID, return the corresponding instrument."""
    if ipppssoot.lower() in INSTRUMENTS:
        return ipppssoot.lower()
    else:
        return IPPPSSOOT_INSTR.get(ipppssoot.upper()[0])

# -----------------------------------------------------------------------------


def get_output_path(output_uri,  ipppssoot):
    """
    >>> get_output_path("s3://temp/batch-2020-02-13T10:33:00", "IC0B02020")
    's3://temp/batch-2020-02-13T10:33:00/wfc3/IC0B02020'
    """
    instrument_name = get_instrument(ipppssoot)
    return output_uri + "/" + instrument_name + "/" + ipppssoot

# -------------------------------------------------------------


def upload_filepath(filepath, s3_filepath):
    """Given `filepath` to upload, copy it to `s3_filepath` which effectively
    describes a directory in S3 storage.
    """
    client = boto3.client('s3')
    if s3_filepath.startswith("s3://"):
        s3_filepath = s3_filepath[5:]
    parts = s3_filepath.split("/")
    bucket, objectname = parts[0], "/".join(parts[1:])
    with open(filepath, "rb") as f:
        client.upload_fileobj(f, bucket, objectname)

# -----------------------------------------------------------------------------


class InstrumentManager:
    instrument_name = None     # abstract class
    download_suffixes = None
    ignore_err_nums = []

    def __init__(self, ipppssoot, output_uri):
        self.ipppssoot = ipppssoot
        self.output_uri = output_uri

    # .............................................................

    def raw_files(self, files):
        return [f for f in files if "_raw" in f]

    def assoc_files(self, files):
        return [f for f in files if f.endswith("_asn.fits")]

    def unassoc_files(self, files):  # can be overriden by subclasses
        return self.raw_files(files)

    # .............................................................

    def divider(self, *args, dash=">"):
        assert len(dash) == 1
        msg = " ".join([str(a) for a in args])
        dashes = (100-len(msg)-2)
        log.info(dash * dashes)
        log.info(
            dash*5,
            self.ipppssoot, msg,
            dash*(dashes-6-len(self.ipppssoot)-len(msg)-1))

    def run(self, cmd, *args):
        cmd = tuple(cmd.split()) + args  # Handle stage values with switches.
        self.divider("Running:", cmd)
        err = subprocess.call(cmd)
        if err in self.ignore_err_nums:
            log.info("Ignoring error status =", err)
        elif err:
            log.error(self.ipppssoot, "Command:", repr(cmd), "exited with error status:", err)
            sys.exit(1)     # should be 0-127,  higher err val's like 512 are truncated to 0 by shells

    # .............................................................

    def main(self):
        """Perform all processing steps for basic calibration processing:
        1. download uncalibrated data
        2. assign bestrefs (and potentially download)
        3. perform CAL processing
        4. copy outputs to S3
        """
        self.divider(
            "Started processing for", self.instrument_name, self.ipppssoot)

        input_files = self.dowload()

        self.assign_bestrefs(input_files)

        self.process(input_files)

        self.output_files()

        self.divider(
            "Completed processing for", self.instrument_name, self.ipppssoot)

    def dowload(self):
        self.divider("Retrieving data files for:", self.download_suffixes)
        files = retrieve_observation(self.ipppssoot, suffix=self.download_suffixes)
        self.divider("Download data complete.")
        return list(sorted(files))

    def assign_bestrefs(self, files):
        self.divider("Computing bestrefs and downloading references.", files)
        bestrefs_files = self.raw_files(files)
        bestrefs.assign_bestrefs(bestrefs_files, sync_references=True)
        self.divider("Bestrefs complete.")

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

    def output_files(self):
        if self.output_uri in [None, "none"]:
            return
        outputs = glob.glob("*.fits")
        outputs += glob.glob("*.tra")
        self.divider("Saving outputs:", self.output_uri, outputs)
        output_path = get_output_path(self.output_uri, self.ipppssoot)
        for filename in outputs:
            upload_filename(filename, output_path + "/" + filename)
        self.divider("Saving outputs complete.")

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


class CosManager(InstrumentManager):
    instrument_name = "cos"
    download_suffixes = ["ASN", "RAW", "EPC", "RAWACCUM", "RAWACCUM_A", "RAWACCUM_B", "RAWACQ", "RAWTAG", "RAWTAG_A", "RAWTAG_B"]
    stage1 = "calcos"
    stage2 = None
    ignore_err_nums = [
        5,    # Ignore calcos errors from RAWACQ
    ]

    def unassoc_files(self, files):
        return super(CosManager, self).raw_files(files)[:1]   # return only first file


class StisManager(InstrumentManager):
    instrument_name = "stis"
    download_suffixes = ["ASN", "RAW", "EPC", "TAG", "WAV"]
    stage1 = "cs0.e -tv"
    stage2 = None

    def process(self, files):
        raw = [f for f in files if f.endswith("_raw.fits")]
        wav = [f for f in files if f.endswith("_wav.fits")]
        if raw:
            self.run(self.stage1, *raw)
        else:
            self.run(self.stage1, *wav)

    def raw_files(self, files):
        return [f for f in files if f.endswith(('_raw.fits','_wav.fits','_tag.fits'))]

# ............................................................................

MANAGERS = {
    "acs": AcsManager,
    "cos": CosManager,
    "stis": StisManager,
    "wfc3": Wfc3Manager,
}


def get_instrument_manager(ipppssoot, output_uri):
    """Given and `ipppssoot` and `output_uri`,  determine
    the appropriate instrument manager from the `ipppssoot`
    and construct and return it.
    """
    instrument = get_instrument(ipppssoot)
    manager = MANAGERS[instrument](ipppssoot, output_uri)
    return manager

# -----------------------------------------------------------------------------


def process(ipppssoot, output_uri):
    """Given an `ipppssoot` and `output_uri` where products should be stored,
    perform all required processing steps for the `ipppssoot`,  generate
    previews of output products,  and store all products and previews relative
    to `output_uri`.
    """
    manager = get_instrument_manager(ipppssoot, output_uri)
    manager.main()

# -----------------------------------------------------------------------------


def process_ipppssoots(ipppssoots, output_uri=None):
    for ipppssoot in ipppssoots:
        process(ipppssoot, output_uri)

# -----------------------------------------------------------------------------


def test():
    from hstdputils import process
    import doctest
    return doctest.testmod(process)

# -----------------------------------------------------------------------------


if __name__ == "__main__":
    if  len(sys.argv) < 3:
        print("usage:  process.py  <output_uri>   <ipppssoot's...>")
        sys.exit(1)
    output_uri = sys.argv[1]
    ipppssoots = sys.argv[2:]
    if output_uri.lower() == "none":
        output_uri = None
    process_ipppssoots(ipppssoots, output_uri)
