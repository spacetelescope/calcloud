#! /usr/bin/env python
# -*-python-*-

"""This tool pulls down Docker image scan reports from ECR based on
the current environment which is used to identify the image.

Run "image-scan-report --help" for usage information.

The result of the report is a YAML file limited to CVE's which are
at the minimum severity level or greater.

Exit status:
    0  scan complete, no fatal vulnerabilities (nominally CRITICAL or HIGH)
    3  scan complete, fatal vulnerabilities found
    anything else  scan results could not be obtained
"""

import sys
import os
import subprocess
import json

# import yaml
import copy
import argparse
import time

SEVERITY_LEVELS = {
    "CRITICAL": ["CRITICAL"],
    "HIGH": ["CRITICAL", "HIGH"],
    "MEDIUM": ["CRITICAL", "HIGH", "MEDIUM"],
    "LOW": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    "INFORMATIONAL": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
    "ALL": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
}

EXIT_OK = 0
EXIT_ERROR = 2
EXIT_VULNERABLE = 3

# Basic scanning will report COMPLETE when scan is done.
# Enhanced scanning will report ACTIVE when the initial scan is done, and then it will continue
# to monitor for CVEs that may affect this image.
# The AWS team sets whether we are using basic or enhanced scanning, so we need to look for both statuses here.
# The scan is done if the status is either COMPLETE or ACTIVE.
SCAN_DONE_STATUSES = ("COMPLETE", "ACTIVE")
SCAN_PENDING_STATUSES = ("IN_PROGRESS", "PENDING")
SCAN_POLL_SECONDS = 10


class ScanError(Exception):
    pass


def run(cmd, cwd=".", env=None):
    result = subprocess.run(
        cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
        cwd=cwd,
        env=env,
    )  # maybe succeeds
    return result.stdout


def _get_scan_results(image_digest, image_tag):
    """Issue an AWS command to dump the ECR scan results as JSON, load the
    JSON,  and return the resulting dict.
    """
    image_repo = os.environ["IMAGE_REPO"]
    ecr_account_to_use = os.environ["ECR_ACCOUNT_ID"]

    image_id_arg = f"imageTag={image_tag}"
    if image_digest:
        image_id_arg = f"imageDigest={image_digest}"

    print(
        f"Fetching ECR vulnerability scan for registry={ecr_account_to_use} repo={image_repo} tag={image_tag}",
        file=sys.stderr,
    )

    # This uses hst-repro-cross-account-ECR-access which is a role in the ECR account.
    # You cannot run describe-image-scan-findings cross account, you have to use a role in the other account.
    # The CLI's automatic pagination fetches and merges every page of findings.
    scan_results = run(
        f"aws ecr describe-image-scan-findings "
        f"--registry-id {ecr_account_to_use} "
        f"--repository-name {image_repo} "
        f"--image-id {image_id_arg}",
        env=dict(os.environ) | {"AWS_PROFILE": "hst-repro-cross-account-ECR-access"},
    )

    # print("Scan Results")
    # print(scan_results)

    return json.loads(scan_results)


def get_scan_results(image_digest):
    return _get_scan_results(image_digest, os.environ["AMIROTATION_ECR_TAG_UNSCANNED"])


def limit_levels(report_levels, fail_levels, full_results):
    """Only report findings with statuses in `report_levels`.
    Only report a failed scan if there are findings with statuses in `fail_levels`.
    Assume `full_results` contains everything returned from ECR which may include
    LOW or INFORMATIONAL CVE's which are normally ignored when scanning for MEDIUM and higher.
    """
    results_to_report = copy.deepcopy(full_results)
    scan_findings = results_to_report.setdefault("imageScanFindings", {})
    results_to_report["overall_status"] = "OK"
    listed_fatal_count = 0
    for key in ("findings", "enhancedFindings"):
        if key not in scan_findings:
            continue
        listed_fatal_count += sum(1 for x in scan_findings[key] if x["severity"] in fail_levels)
        scan_findings[key] = [x for x in scan_findings[key] if x["severity"] in report_levels]
    severity_counts = scan_findings.get("findingSeverityCounts")
    if severity_counts is None:
        results_to_report["fatal_count"] = listed_fatal_count
    else:
        results_to_report["fatal_count"] = sum(
            severity_counts.get(level, 0) for level in fail_levels
        )
    if results_to_report["fatal_count"]:
        results_to_report["overall_status"] = "FAILED"
    return results_to_report


def get_report_dict(report_levels, fail_levels, image_digest, timeout):
    """Wait for the ECR scan to finish and return its findings limited to
    `report_levels`. Raises ScanError if results cannot be obtained.
    """
    deadline = time.monotonic() + timeout
    while True:
        try:
            vulnerabilities = get_scan_results(image_digest)
        except subprocess.CalledProcessError as exc:
            # A scan may not exist yet right after the push; anything else is a real error.
            if "ScanNotFoundException" not in (exc.output or ""):
                raise ScanError(
                    f"describe-image-scan-findings failed with exit status {exc.returncode}:\n"
                    f"{(exc.output or '').strip()}"
                ) from exc
            status = "NOT_STARTED"
        else:
            scan_status = vulnerabilities.get("imageScanStatus", {})
            status = scan_status.get("status")
            if status in SCAN_DONE_STATUSES:
                return limit_levels(report_levels, fail_levels, vulnerabilities)
            if status not in SCAN_PENDING_STATUSES:
                raise ScanError(f"ECR scan ended with status {status}: {scan_status.get('description', '')}")

        if time.monotonic() >= deadline:
            hint = " Is scan-on-push enabled for this repository?" if status == "NOT_STARTED" else ""
            raise ScanError(f"Timed out after {timeout}s waiting for ECR scan, last status: {status}.{hint}")
        print(f"Waiting for ECR scan, prior status: {status}", file=sys.stderr)
        sys.stderr.flush()
        time.sleep(SCAN_POLL_SECONDS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-levels",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "ALL"],
        action="store",
        help="Report findings at this security level and higher, e.g. MEDIUM",
        default="MEDIUM",
    )
    parser.add_argument(
        "--fail-levels",
        choices=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "ALL"],
        action="store",
        help="Fail if there are findings at this security level and higher, e.g. HIGH",
        default="HIGH",
    )
    parser.add_argument(
        "--image-digest",
        dest="image_digest",
        default=None,
        help="Digest of image to scan, e.g. sha256:*",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Seconds to wait for the ECR scan to complete",
    )
    args = parser.parse_args()

    report_levels = SEVERITY_LEVELS[args.report_levels.upper()]
    fail_levels = SEVERITY_LEVELS[args.fail_levels.upper()]

    try:
        reduced = get_report_dict(report_levels, fail_levels, args.image_digest, args.timeout)
    except ScanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    # print(reduced)
    # print(yaml.dump(reduced))

    if reduced["overall_status"] == "FAILED":
        print(f"Scan found {reduced['fatal_count']} finding(s) at levels {fail_levels}", file=sys.stderr)
        sys.exit(EXIT_VULNERABLE)
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
