import argparse
import os
import subprocess
import logging
import json
import glob

from astropy.io import fits

from . import log

# -----------------------------------------------------------------------------------------------------------------

LOGGER = logging.getLogger(__name__)

AUTOSCALE=99.5

OUTPUT_FORMATS = [
    ("_thumb", 128),
    ("", -1)
]


# -----------------------------------------------------------------------------------------------------------------

def generate_image_preview(input_path, output_path, size):
    cmd = [
        "fitscut",
        "--all",
        "--jpg",
        f"--autoscale={AUTOSCALE}",
        "--asinh-scale",
        f"--output-size={size}",
        "--badpix",
        input_path
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode > 0:
        LOGGER.error("fitscut failed for %s with status %s: %s", input_path, process.returncode, stderr)
        raise RuntimeError()

    with open(output_path, "wb") as f:
        f.write(stdout)


def generate_image_previews(input_path, output_dir, filename_base):
    output_paths = []
    for suffix, size in OUTPUT_FORMATS:
        output_path = os.path.join(output_dir, f"{filename_base}{suffix}.jpg")
        try:
            generate_image_preview(input_path, output_path, size)
        except Exception:
            log.info("Preview file (imaging) not generated for", input_path, "with size", size)
        else:
            output_paths.append(output_path)
    return output_paths


def generate_spectral_previews(input_path, output_dir, filename_base):
    log.warning(f"Preview file (spectral) not implemented/generated for {input_path}")
    return []

    # cmd = [
    #     "make_jwst_spec_previews",
    #     "-v", "-o", output_dir, input_path
    # ]
    # try:
    #     output = subprocess.check_output(cmd)
    #     return [p for p in output.split() if filename_base in p and "fits" not in p.lower()]
    # except Exception:
    #     LOGGER.exception("Preview file not generated for %s", input_path)
    #     return []


def generate_previews(input_path, output_dir, filename_base):
    with fits.open(input_path) as hdul:
        naxis = hdul[1].header["NAXIS"]
        ext = hdul[1].header["XTENSION"]

    if naxis == 2 and ext == "BINTABLE":
        return generate_spectral_previews(input_path, output_dir, filename_base)
    elif naxis >= 2 and ext == "IMAGE":
        return generate_image_previews(input_path, output_dir, filename_base)
    else:
        log.warning("Unable to determine FITS file type")
        return []


def split_uri(uri):
    assert uri.startswith("s3://")
    return uri.replace("s3://", "").split("/", 1)


def list_fits_uris(uri_prefix):
    bucket_name, key = split_uri(uri_prefix)
    result = subprocess.check_output([
        "aws", "s3api", "list-objects",
        "--bucket", bucket_name,
        "--prefix", key,
        "--output", "json",
        "--query", "Contents[].Key"
    ])
    return [f"s3://{bucket_name}/{k}" for k in json.loads(result) if k.lower().endswith(".fits")]

def main(args, outdir="."):
    """Generates previews based on a file system or S3 input directory
    and an S3 output directory both specified in args.
    """
    if args.input_uri_prefix.startswith("s3://"):
        input_uris = list_fits_uris(args.input_uri_prefix)
        log.info("Processing", len(input_uris), "FITS files from prefix", args.input_uri_prefix)
        for input_uri in input_uris:
            log.info("Fetching", input_uri)
            filename = os.path.basename(input_uri)
            input_path = os.path.join(outdir, filename)
            subprocess.check_call([
                "aws", "s3", "cp", input_uri, input_path
            ])
    else:
        input_uris = glob.glob(args.input_uri_prefix + "/*.fits")
        log.info("Processing", len(input_uris), "FITS files from prefix", args.input_uri_prefix)
    for input_uri in input_uris:
        filename = os.path.basename(input_uri)
        input_path = os.path.join(outdir, filename)
        filename_base, _ = os.path.splitext(filename)
        log.info("Geneating previews for", input_path)
        output_paths = generate_previews(input_path, outdir, filename_base)
        log.info("Generated", len(output_paths), "output files")
        for output_path in output_paths:
            if output_path.startswith("s3://"):  # is set to "none" for local use
                output_uri = os.path.join(args.output_uri_prefix, os.path.basename(output_path))
                log.info("Uploading", output_path, "to", output_uri)
                subprocess.check_call([
                    "aws", "s3", "cp", "--quiet", output_path, output_uri
                ])

def parse_args():
    parser = argparse.ArgumentParser(description="Create image and spectral previews")

    parser.add_argument("input_uri_prefix", help="S3 URI prefix or local directory containing FITS images that require previews")
    parser.add_argument("output_uri_prefix", help="S3 URI prefix for writing previews")

    return parser.parse_args()


if __name__ == "__main__":
    main(parse_args())
