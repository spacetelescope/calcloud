"""Record provenance for a completed build-ID image set.

Run after all three final ECR tags have been pushed. The default is a dry run;
pass --apply to write package inventories and the manifest to the dev state bucket.
"""

import argparse
from datetime import datetime, timezone
import json
import os
import re
import shlex
import subprocess

import boto3
from botocore.exceptions import ClientError


IMAGE_TAG_VARIABLES = {
    "batch": "CALDP_ECR_TAG",
    "predict": "PREDICT_ECR_TAG",
    "amirotation": "AMIROTATION_ECR_TAG",
}
BASE_IMAGE_VARIABLES = {
    "batch": ("CAL_BASE_IMAGE_REF", "CAL_BASE_IMAGE_RESOLVED"),
    "predict": ("PREDICT_BASE_IMAGE_REF", "PREDICT_BASE_IMAGE_RESOLVED"),
    "amirotation": ("AMIROTATION_BASE_IMAGE_REF", "AMIROTATION_BASE_IMAGE_RESOLVED"),
}
BUILD_ID_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\.[0-9]{2}$")
BASE_DIGEST_PATTERN = re.compile(r"@(?P<digest>sha256:[a-f0-9]{64})$")
OS_INSPECTION_SCRIPT = r"""set -eu
printf '__CALCLOUD_OS_RELEASE__\n'
cat /etc/os-release 2>/dev/null || true
printf '\n__CALCLOUD_SYSTEM_RELEASE__\n'
cat /etc/system-release 2>/dev/null || true
printf '\n__CALCLOUD_PACKAGES__\n'
if command -v rpm >/dev/null 2>&1; then
    rpm -qa --qf '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n' | sort
elif command -v dpkg-query >/dev/null 2>&1; then
    dpkg-query -W -f='${binary:Package}=${Version}\n' | sort
elif command -v apk >/dev/null 2>&1; then
    apk info -v | sort
else
    echo '__NO_PACKAGE_MANAGER__'
fi
"""


def get_required_environment(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required build variable {name} is missing")
    return value


def run_git(repository, *arguments, check=True):
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=check,
        capture_output=True,
        text=True,
    )


def get_git_provenance(repository, version):
    commit = run_git(repository, "rev-parse", "HEAD").stdout.strip()
    branch = run_git(repository, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if branch.returncode == 0:
        reference = f"refs/heads/{branch.stdout.strip()}"
    else:
        tags = set(run_git(repository, "tag", "--points-at", "HEAD").stdout.splitlines())
        matching_tags = [tag for tag in (f"v{version}", version) if tag in tags]
        if matching_tags:
            reference = f"refs/tags/{matching_tags[0]}"
        elif len(tags) == 1:
            reference = f"refs/tags/{next(iter(tags))}"
        else:
            reference = f"commit:{commit}"
    return reference, commit


def describe_image(ecr, registry_id, repository, tag):
    response = ecr.describe_images(
        registryId=registry_id,
        repositoryName=repository,
        imageIds=[{"imageTag": tag}],
    )
    details = response.get("imageDetails", [])
    if len(details) != 1 or not details[0].get("imageDigest"):
        raise RuntimeError(f"Could not resolve a single ECR digest for tag {tag}")
    return details[0]["imageDigest"]


def parse_os_release(text):
    values = {}
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if not separator:
            continue
        parsed = shlex.split(value)
        values[key] = parsed[0] if parsed else ""
    return values


def inspect_image(image_uri):
    result = subprocess.run(
        ["docker", "run", "--rm", "--network", "none", "--entrypoint", "/bin/sh", image_uri, "-c", OS_INSPECTION_SCRIPT],
        check=True,
        capture_output=True,
        text=True,
        timeout=600,
    )
    _, os_separator, remainder = result.stdout.partition("__CALCLOUD_OS_RELEASE__\n")
    os_text, system_marker, remainder = remainder.partition("\n__CALCLOUD_SYSTEM_RELEASE__\n")
    system_text, packages_marker, package_text = remainder.partition("\n__CALCLOUD_PACKAGES__\n")
    if not os_separator or not system_marker or not packages_marker:
        raise RuntimeError(f"Could not parse OS and package information from {image_uri}")

    os_release = parse_os_release(os_text)
    packages = sorted(line.strip() for line in package_text.splitlines() if line.strip())
    if "__NO_PACKAGE_MANAGER__" in packages or not packages:
        raise RuntimeError(f"Could not collect package inventory from {image_uri}")

    distribution = os_release.get("NAME") or os_release.get("ID")
    release = os_release.get("VERSION_ID")
    system_release = system_text.strip()
    patch_level = system_release or os_release.get("VERSION")
    if not distribution or not release or not patch_level:
        raise RuntimeError(f"Could not determine OS release details from {image_uri}")
    return {
        "distribution": distribution,
        "release": release,
        "patchLevel": patch_level,
    }, packages, os_release, system_release


def get_existing_object(s3, bucket, key):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as error:
        error_code = error.response.get("Error", {}).get("Code")
        status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if error_code == "NoSuchBucket":
            raise RuntimeError(f"Manifest bucket does not exist: {bucket}") from error
        if error_code in {"404", "NoSuchKey", "NotFound"} or (error_code is None and status_code == 404):
            return None
        raise
    try:
        return response["Body"].read()
    finally:
        response["Body"].close()


def canonical_manifest(body):
    manifest = json.loads(body)
    manifest.pop("recordedAt", None)
    return json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write package inventories and manifest to S3.")
    args = parser.parse_args()

    build_id = get_required_environment("IMAGE_BUILD_ID")
    if not BUILD_ID_PATTERN.fullmatch(build_id):
        raise RuntimeError("IMAGE_BUILD_ID must match YYYY-MM-DD.NN")

    repository_uri = get_required_environment("repo_url")
    registry_id = get_required_environment("ECR_ACCOUNT_ID")
    repository = get_required_environment("IMAGE_REPO")
    image_tags = {image_type: get_required_environment(variable) for image_type, variable in IMAGE_TAG_VARIABLES.items()}
    calcloud_version = get_required_environment("CALCLOUD_VER")
    caldp_version = get_required_environment("CALDP_VER")
    calcloud_repo = get_required_environment("CALCLOUD_BUILD_DIR")
    caldp_repo = get_required_environment("CALDP_BUILD_DIR")
    git_sources = {
        "calcloud": get_git_provenance(calcloud_repo, calcloud_version),
        "caldp": get_git_provenance(caldp_repo, caldp_version),
    }

    session = boto3.Session(
        profile_name=os.environ.get("AWS_PROFILE", "hst_reprocessing_admin_role"),
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )
    ssm = session.client("ssm")
    ecr = session.client("ecr")
    s3 = session.client("s3")
    bucket_value = ssm.get_parameter(Name="/s3/tfstate")["Parameter"]["Value"]
    bucket = bucket_value.rstrip("/").split(":")[-1].split("/")[-1]
    if not bucket:
        raise RuntimeError("SSM parameter /s3/tfstate did not contain a bucket name")

    manifest_key = os.environ.get("IMAGE_RELEASE_MANIFEST_KEY") or f"calcloud/releases/{build_id}/manifest.json"
    expected_manifest_key = f"calcloud/releases/{build_id}/manifest.json"
    if manifest_key != expected_manifest_key:
        raise RuntimeError(f"IMAGE_RELEASE_MANIFEST_KEY must be {expected_manifest_key}")
    if get_existing_object(s3, bucket, manifest_key) is not None:
        raise RuntimeError(f"Manifest already exists at s3://{bucket}/{manifest_key}")

    image_specs = {
        "batch": {
            "baseRef": "CAL_BASE_IMAGE_REF",
            "baseResolved": "CAL_BASE_IMAGE_RESOLVED",
            "sources": {"caldp"},
        },
        "predict": {
            "baseRef": "PREDICT_BASE_IMAGE_REF",
            "baseResolved": "PREDICT_BASE_IMAGE_RESOLVED",
            "sources": {"calcloud"},
        },
        "amirotation": {
            "baseRef": "AMIROTATION_BASE_IMAGE_REF",
            "baseResolved": "AMIROTATION_BASE_IMAGE_RESOLVED",
            "sources": {"calcloud"},
        },
    }
    images = {}
    objects_to_write = {}
    for image_type, tag in image_tags.items():
        digest = describe_image(ecr, registry_id, repository, tag)
        base_ref = get_required_environment(image_specs[image_type]["baseRef"])
        base_resolved = get_required_environment(image_specs[image_type]["baseResolved"])
        digest_match = BASE_DIGEST_PATTERN.search(base_resolved)
        if not digest_match:
            raise RuntimeError(f"Resolved base image reference is not digest-pinned: {base_resolved}")

        image_uri = f"{repository_uri}@{digest}"
        os_data, packages, os_release, system_release = inspect_image(image_uri)
        inventory_key = f"calcloud/releases/{build_id}/packages/{image_type}.json"
        inventory = {
            "schemaVersion": 1,
            "buildId": build_id,
            "imageType": image_type,
            "imageDigest": digest,
            "osRelease": os_release,
            "systemRelease": system_release,
            "packages": packages,
        }
        objects_to_write[inventory_key] = json.dumps(inventory, indent=2, sort_keys=True).encode("utf-8")

        relevant_sources = image_specs[image_type]["sources"]
        images[image_type] = {
            "repository": repository_uri,
            "buildTag": tag,
            "legacyTag": None,
            "digest": digest,
            "sourceVersions": {
                "calcloud": calcloud_version if "calcloud" in relevant_sources else None,
                "caldp": caldp_version if "caldp" in relevant_sources else None,
            },
            "sourceRefs": {
                name: git_sources[name][0] if name in relevant_sources else None for name in ("calcloud", "caldp")
            },
            "sourceCommits": {
                name: git_sources[name][1] if name in relevant_sources else None for name in ("calcloud", "caldp")
            },
            "baseImage": {"reference": base_ref, "digest": digest_match.group("digest")},
            "os": {**os_data, "packageInventoryS3Key": inventory_key},
        }

    manifest = {
        "schemaVersion": 1,
        "buildId": build_id,
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "origin": "built",
        "images": images,
    }
    objects_to_write[manifest_key] = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")

    uploads = []
    for key, body in objects_to_write.items():
        existing_body = get_existing_object(s3, bucket, key)
        if existing_body is None:
            uploads.append((key, body))
        elif key == manifest_key:
            if canonical_manifest(existing_body) != canonical_manifest(body):
                raise RuntimeError(f"Existing manifest conflicts with this build: s3://{bucket}/{key}")
        elif existing_body != body:
            raise RuntimeError(f"Existing package inventory conflicts with this build: s3://{bucket}/{key}")

    print(f"Build ID: {build_id}")
    for image_type, image in images.items():
        print(f"{image_type}: {image['buildTag']} -> {image['digest']}")
        print(f"  base: {image['baseImage']['reference']} -> {image['baseImage']['digest']}")
        print(f"  OS: {image['os']['distribution']} {image['os']['release']} ({image['os']['patchLevel']})")
    print(f"Manifest: s3://{bucket}/{manifest_key}")
    print(f"Objects to write: {len(uploads)}")

    if not args.apply:
        print("Dry run: no S3 objects were changed. Pass --apply to write the manifest and inventories.")
        return

    for key, body in uploads:
        try:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=body,
                ContentType="application/json",
                IfNoneMatch="*",
            )
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code not in {"PreconditionFailed", "ConditionalRequestConflict"}:
                raise
            existing_body = get_existing_object(s3, bucket, key)
            if existing_body != body and not (
                key == manifest_key
                and existing_body is not None
                and canonical_manifest(existing_body) == canonical_manifest(body)
            ):
                raise RuntimeError(f"S3 object changed during manifest write: s3://{bucket}/{key}") from error
    print("Release manifest and package inventories written.")


if __name__ == "__main__":
    main()