"""Migrate the source image set selected by deploy_vars.sh to build-ID tags.

Run from the terraform directory after sourcing deploy_vars.sh with
IMAGE_BUILD_ID empty. The three exported legacy tags must share one suffix.
"""

import argparse
from datetime import datetime, timezone
import json
import os
import re

import boto3
from botocore.exceptions import ClientError


IMAGE_TAG_VARIABLES = {
    "batch": "LEGACY_CALDP_ECR_TAG",
    "predict": "LEGACY_PREDICT_ECR_TAG",
    "amirotation": "LEGACY_AMIROTATION_ECR_TAG",
}
LEGACY_SUFFIX_PATTERN = re.compile(r"^CALCLOUD_.+-CALDP_.+-BASE_.+$")
BUILD_TAG_PATTERN = re.compile(r"^(batch|predict|amirotation)-build-(\d{4}-\d{2}-\d{2})\.(\d{2})$")


def get_required_environment(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required deployment variable {name} is missing")
    return value


def describe_image(ecr, registry_id, repository, tag):
    try:
        response = ecr.describe_images(
            registryId=registry_id,
            repositoryName=repository,
            imageIds=[{"imageTag": tag}],
        )
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") == "ImageNotFoundException":
            return None
        raise

    details = response.get("imageDetails", [])
    return details[0] if details else None


def describe_tag(ecr, registry_id, repository, tag):
    image = describe_image(ecr, registry_id, repository, tag)
    return image["imageDigest"] if image else None


def get_source_tags():
    image_tags = {
        image_type: get_required_environment(variable)
        for image_type, variable in IMAGE_TAG_VARIABLES.items()
    }
    suffixes = set()
    for image_type, tag in image_tags.items():
        prefix = f"{image_type}-"
        if not tag.startswith(prefix):
            raise RuntimeError(f"Source tag {tag} must start with {prefix}")
        suffixes.add(tag[len(prefix) :])

    if len(suffixes) != 1:
        raise RuntimeError("The three legacy source tags do not share the same composite suffix")
    suffix = suffixes.pop()
    if not LEGACY_SUFFIX_PATTERN.fullmatch(suffix):
        raise RuntimeError(f"Legacy tag suffix has an unexpected format: {suffix}")
    configured_suffix = get_required_environment("LEGACY_COMMON_IMAGE_TAG")
    if suffix != configured_suffix:
        raise RuntimeError("Legacy source tags do not match LEGACY_COMMON_IMAGE_TAG")
    return image_tags, suffix


def build_date_from_push_times(image_records):
    dates = set()
    for image_type, record in image_records.items():
        pushed_at = record["pushedAt"]
        if pushed_at is None:
            raise RuntimeError(f"ECR did not report an imagePushedAt time for {image_type}")
        if pushed_at.tzinfo is None:
            pushed_at = pushed_at.replace(tzinfo=timezone.utc)
        dates.add(pushed_at.astimezone(timezone.utc).date().isoformat())

    if len(dates) != 1:
        details = ", ".join(
            f"{image_type}={record['pushedAt'].isoformat()}" for image_type, record in image_records.items()
        )
        raise RuntimeError(f"Source images were pushed on different UTC dates: {details}")
    return dates.pop()


def next_build_id(ecr, s3, registry_id, repository, bucket, build_date):
    used_sequences = set()
    ecr_paginator = ecr.get_paginator("describe_images")
    for page in ecr_paginator.paginate(registryId=registry_id, repositoryName=repository):
        for image in page.get("imageDetails", []):
            for tag in image.get("imageTags", []):
                match = BUILD_TAG_PATTERN.fullmatch(tag)
                if match and match.group(2) == build_date:
                    used_sequences.add(int(match.group(3)))

    s3_paginator = s3.get_paginator("list_objects_v2")
    prefix = f"calcloud/releases/build-{build_date}."
    manifest_pattern = re.compile(rf"^calcloud/releases/build-{re.escape(build_date)}\.(\d{{2}})/manifest\.json$")
    for page in s3_paginator.paginate(Bucket=bucket, Prefix=prefix):
        for item in page.get("Contents", []):
            match = manifest_pattern.fullmatch(item["Key"])
            if match:
                used_sequences.add(int(match.group(1)))

    for sequence in range(1, 100):
        if sequence not in used_sequences:
            return f"build-{build_date}.{sequence:02d}"
    raise RuntimeError(f"No unused build ID sequence remains for {build_date}")


def get_source_image(ecr, registry_id, repository, tag):
    response = ecr.batch_get_image(
        registryId=registry_id,
        repositoryName=repository,
        imageIds=[{"imageTag": tag}],
    )
    if response.get("failures") or not response.get("images"):
        raise RuntimeError(f"Could not retrieve source image tagged {tag}: {response.get('failures')}")
    return response["images"][0]


def has_manifest(s3, bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as error:
        response = error.response
        code = response.get("Error", {}).get("Code")
        if code in {"404", "NoSuchKey", "NotFound"} or response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
            return False
        raise


def make_manifest(build_id, repository_uri, image_tags, image_records):
    calcloud_version = get_required_environment("CALCLOUD_VER")
    caldp_version = get_required_environment("CALDP_VER")
    cal_base_image = get_required_environment("CAL_BASE_IMAGE")
    images = {}

    for image_type, source_tag in image_tags.items():
        record = image_records[image_type]
        images[image_type] = {
            "repository": repository_uri,
            "buildTag": f"{image_type}-{build_id}",
            "legacyTag": source_tag,
            "digest": record["digest"],
            "sourceVersions": {"calcloud": calcloud_version, "caldp": caldp_version},
            "sourceRefs": {"calcloud": None, "caldp": None},
            "sourceCommits": {"calcloud": None, "caldp": None},
            "baseImage": {
                "reference": cal_base_image if image_type == "batch" else None,
                "digest": None,
            },
            "os": {
                "distribution": None,
                "release": None,
                "patchLevel": None,
                "packageInventoryS3Key": None,
            },
        }

    return {
        "schemaVersion": 1,
        "buildId": build_id,
        "recordedAt": datetime.now(timezone.utc).isoformat(),
        "origin": "migrated",
        "images": images,
    }


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    registry_id = get_required_environment("ECR_ACCOUNT_ID")
    repository = get_required_environment("IMAGE_REPO")
    repository_uri = get_required_environment("repo_url")
    image_tags, legacy_suffix = get_source_tags()

    session = boto3.Session(
        profile_name=os.environ.get("AWS_PROFILE", "hst_reprocessing_admin_role"),
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )
    ssm = session.client("ssm")
    ecr = session.client("ecr")
    s3 = session.client("s3")

    bucket = ssm.get_parameter(Name="/s3/tfstate")["Parameter"]["Value"]
    bucket = bucket.removeprefix("s3://").rstrip("/")
    if not bucket:
        raise RuntimeError("SSM parameter /s3/tfstate did not contain a bucket name")

    image_records = {}
    for image_type, source_tag in image_tags.items():
        source_details = describe_image(ecr, registry_id, repository, source_tag)
        if source_details is None:
            raise RuntimeError(f"Could not find source image tagged {source_tag}")
        source_image = get_source_image(ecr, registry_id, repository, source_tag)
        source_digest = source_image["imageId"]["imageDigest"]
        if source_details["imageDigest"] != source_digest:
            raise RuntimeError(f"ECR returned inconsistent digest information for {source_tag}")
        image_records[image_type] = {
            "source": source_image,
            "digest": source_digest,
            "pushedAt": source_details.get("imagePushedAt"),
        }

    build_date = build_date_from_push_times(image_records)
    build_id = next_build_id(ecr, s3, registry_id, repository, bucket, build_date)
    target_tags = {image_type: f"{image_type}-{build_id}" for image_type in IMAGE_TAG_VARIABLES}
    manifest_key = f"calcloud/releases/{build_id}/manifest.json"
    if has_manifest(s3, bucket, manifest_key):
        raise RuntimeError(f"Manifest already exists at s3://{bucket}/{manifest_key}")

    for image_type, source_tag in image_tags.items():
        source_digest = image_records[image_type]["digest"]
        target_tag = target_tags[image_type]
        target_digest = describe_tag(ecr, registry_id, repository, target_tag)
        if target_digest and target_digest != source_digest:
            raise RuntimeError(
                f"Target tag {target_tag} already points to {target_digest}, not source digest {source_digest}"
            )
        image_records[image_type]["alreadyTagged"] = target_digest == source_digest

    manifest = make_manifest(build_id, repository_uri, image_tags, image_records)
    print(f"Selected legacy suffix: {legacy_suffix}")
    print(f"ECR push date: {build_date}; generated build ID: {build_id}")
    print(f"Manifest: s3://{bucket}/{manifest_key}")
    for image_type, source_tag in image_tags.items():
        record = image_records[image_type]
        state = "already tagged" if record["alreadyTagged"] else "will tag"
        print(f"{state}: {source_tag} -> {target_tags[image_type]} ({record['digest']})")

    if args.dry_run:
        print("Dry run: no ECR tags or S3 objects were changed.")
        return

    for image_type, source_tag in image_tags.items():
        record = image_records[image_type]
        if record["alreadyTagged"]:
            continue
        image = record["source"]
        request = {
            "registryId": registry_id,
            "repositoryName": repository,
            "imageTag": target_tags[image_type],
            "imageManifest": image["imageManifest"],
        }
        if image.get("imageManifestMediaType"):
            request["imageManifestMediaType"] = image["imageManifestMediaType"]
        try:
            ecr.put_image(**request)
        except ecr.exceptions.ImageAlreadyExistsException:
            target_digest = describe_tag(ecr, registry_id, repository, target_tags[image_type])
            if target_digest != record["digest"]:
                raise RuntimeError(f"Target tag {target_tags[image_type]} was concurrently assigned to another image")

    for image_type, target_tag in target_tags.items():
        target_digest = describe_tag(ecr, registry_id, repository, target_tag)
        if target_digest != image_records[image_type]["digest"]:
            raise RuntimeError(f"Digest verification failed for target tag {target_tag}")

    s3.put_object(
        Bucket=bucket,
        Key=manifest_key,
        Body=json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8"),
        ContentType="application/json",
        IfNoneMatch="*",
    )
    print("Migration complete; all build-ID tags match their source digests and the manifest was written.")


if __name__ == "__main__":
    main()