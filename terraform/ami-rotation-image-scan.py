#! /usr/bin/env python
# -*-python-*-

"""This tool pulls down Docker image scan reports from ECR based on
the current environment which is used to identify the image.

Run "image-scan-report --help" for usage information.

The result of the report is a YAML file limited to CVE's which are
at the minimum severity level or greater.

The exit status of the program reflects the presence or absence of
fatal vulnerabilities,  nominally classified as CRITICAL or HIGH.
"""

import sys
import os
import subprocess
import json
#import yaml
import copy
import argparse
import time


KEEP_LEVELS = {
    "CRITICAL": ["CRITICAL"],
    "HIGH": ["CRITICAL", "HIGH"],
    "MEDIUM": ["CRITICAL", "HIGH", "MEDIUM"],
    "LOW": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    "INFORMATIONAL": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
    "ALL": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
}

FAIL_LEVELS = ["CRITCAL", "HIGH"]


def run(cmd, cwd="."):
    result = subprocess.run(
        cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
        cwd=cwd,
    )  # maybe succeeds
    return result.stdout


def _get_scan_results(image_digest, image_tag):
    """Issue an AWS command to dump the ECR scan results as JSON, load the
    JSON,  and return the resulting dict.
    """
    admin_arn = os.environ["ADMIN_ARN"]
    image_repo = os.environ["IMAGE_REPO"]
    ecr_account_to_use = os.environ["ECR_ACCOUNT_ID"]

    image_id_arg = f"imageTag={image_tag}"
    if image_digest:
        image_id_arg = f"imageDigest={image_digest}"

    print(
        f"Fetching ECR vulnerability scan for registry={ecr_account_to_use} repo={image_repo} tag={image_tag}",
        file=sys.stderr,
    )

    scan_results = run(
        f"awsudo -d 3600 {admin_arn}  aws ecr describe-image-scan-findings "
        f"--no-paginate "
        f"--registry-id {ecr_account_to_use} "
        f"--repository-name {image_repo} "
        f"--image-id {image_id_arg}"
    )

    #print("Scan Results")
    #print(scan_results)

    return json.loads(scan_results)


def get_scan_results(image_digest):
    image_tag = os.environ["AMIROTATION_ECR_TAG_UNSCANNED"]
    try:
        return _get_scan_results(image_digest, image_tag)
    except Exception:
        print(
            f"Failed fetching {image_tag}.  Trying for approved tag.", file=sys.stderr
        )
        if image_tag.endswith("_UNSCANNED"):
            return _get_scan_results(image_digest, image_tag[:len("_UNSCANNED")])
        else:
           raise


def limit_levels(keep_levels, fail_levels, full_results):
    """Only keep findings with statuses in `levels`.  Assume `full_results` contains
    everything returned from ECR which e.g. **may** include LOW or INFORMATIONAL CVE's
    which are normally ignored when scanning for MEDIUM and higher;  remove lower
    priority CVS's from return dict.
    """
    reduced_results = copy.deepcopy(full_results)
    findings = reduced_results["imageScanFindings"]["findings"]
    reduced_results["imageScanFindings"]["findings"] = []
    reduced_results["overall_status"] = "OK"
    for finding in findings:
        if finding["severity"] in keep_levels or "ALL" in keep_levels:
            reduced_results["imageScanFindings"]["findings"].append(finding)
        if finding["severity"] in fail_levels:
            reduced_results["overall_status"] = "FAILED"
    return reduced_results


def get_report_dict(keep_levels, fail_levels, image_digest):
    """Get the overall scan report dict which includes both ECR findings which
    have severities in `levels` and the Ubuntu status string for the CVE for
    Ubuntu `version`.
    """
    sys.stderr.flush()
    vulnerabilities = get_scan_results(image_digest)
    while vulnerabilities["imageScanStatus"]["status"] != "COMPLETE":
        print(
            "Waiting for ECR scan,  prior status:",
            vulnerabilities["imageScanStatus"]["status"],
            file=sys.stderr,
        )
        sys.stderr.flush()
        time.sleep(10)
        vulnerabilities = get_scan_results(image_digest)
    reduced = limit_levels(keep_levels, fail_levels, vulnerabilities)
    return reduced


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--keep-levels",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
        nargs="+",
        action="store",
        help="Minimum severity level, e.g. MEDIUM",
        default="MEDIUM",
    )
    parser.add_argument(
        "--fail-levels",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
        nargs="+",
        action="store",
        help="Minimum severity level, e.g. MEDIUM",
        default="HIGH",
    )
    parser.add_argument(
        "--image-digest",
        dest="image_digest",
        default=None,
        help="Digest of image to scan, e.g. sha256:*",
    )
    args = parser.parse_args()

    keep_levels = KEEP_LEVELS[args.keep_levels.upper()]
    fail_levels = KEEP_LEVELS[args.fail_levels.upper()]

    reduced = get_report_dict(keep_levels, fail_levels, args.image_digest)

    #print(reduced)
    #print(yaml.dump(reduced))

    sys.exit(reduced["overall_status"] == "FAILED")

if __name__ == "__main__":
    main()