"""Copy release manifests and package inventories from the dev bucket to other account buckets.

The source and each destination are specified as AWS profile and bucket
pairs. Use '-' as a profile to use the default AWS credential chain. The
command only uploads objects when --apply is supplied.
"""

import argparse
import json
import os
from pathlib import PurePosixPath

import boto3
from botocore.exceptions import ClientError


MANIFEST_PREFIX = "calcloud/releases/"
MANIFEST_SUFFIX = "/manifest.json"


def normalize_bucket(bucket):
    if bucket.startswith("s3://"):
        return bucket.removeprefix("s3://").rstrip("/")
    if bucket.startswith("arn:aws:s3:::"):
        return bucket.removeprefix("arn:aws:s3:::").rstrip("/")
    return bucket


def make_session(profile, region):
    return boto3.Session(profile_name=profile or None, region_name=region)


def load_source_manifests(s3, bucket):
    manifests = []
    objects = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=MANIFEST_PREFIX):
        for item in page.get("Contents", []):
            key = item["Key"]
            if not key.endswith(MANIFEST_SUFFIX):
                continue

            response = s3.get_object(Bucket=bucket, Key=key)
            try:
                body = response["Body"].read()
            finally:
                response["Body"].close()

            try:
                manifest = json.loads(body)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise RuntimeError(f"Manifest is not valid JSON: s3://{bucket}/{key}") from error

            key_build_id = key[len(MANIFEST_PREFIX) : -len(MANIFEST_SUFFIX)]
            if not isinstance(manifest, dict) or manifest.get("buildId") != key_build_id:
                raise RuntimeError(f"Manifest buildId does not match its S3 key: s3://{bucket}/{key}")
            if manifest.get("schemaVersion") != 1 or not isinstance(manifest.get("images"), dict):
                raise RuntimeError(f"Manifest has an unsupported or invalid structure: s3://{bucket}/{key}")
            manifests.append((key, body, manifest))

            build_prefix = f"{MANIFEST_PREFIX}{key_build_id}/packages/"
            for image_type, image in manifest["images"].items():
                if not isinstance(image, dict):
                    raise RuntimeError(f"Invalid image record in manifest: s3://{bucket}/{key}")
                os_details = image.get("os")
                if os_details is None:
                    continue
                if not isinstance(os_details, dict):
                    raise RuntimeError(f"Invalid OS metadata in manifest: s3://{bucket}/{key}")
                inventory_key = os_details.get("packageInventoryS3Key")
                if inventory_key is None:
                    continue
                if not isinstance(inventory_key, str):
                    raise RuntimeError(f"Invalid package inventory key in manifest: {inventory_key!r}")
                inventory_path = PurePosixPath(inventory_key)
                if not inventory_key.startswith(build_prefix) or inventory_path.is_absolute() or ".." in inventory_path.parts:
                    raise RuntimeError(f"Invalid package inventory key in manifest: {inventory_key!r}")

                inventory_response = s3.get_object(Bucket=bucket, Key=inventory_key)
                try:
                    inventory_body = inventory_response["Body"].read()
                finally:
                    inventory_response["Body"].close()
                try:
                    inventory = json.loads(inventory_body)
                except (UnicodeDecodeError, json.JSONDecodeError) as error:
                    raise RuntimeError(f"Package inventory is not valid JSON: s3://{bucket}/{inventory_key}") from error
                if (
                    not isinstance(inventory, dict)
                    or inventory.get("schemaVersion") != 1
                    or inventory.get("buildId") != key_build_id
                    or inventory.get("imageType") != image_type
                    or inventory.get("imageDigest") != image.get("digest")
                    or not isinstance(inventory.get("packages"), list)
                ):
                    raise RuntimeError(f"Package inventory does not match its manifest: s3://{bucket}/{inventory_key}")
                objects.append((inventory_key, inventory_body, inventory))

    if not manifests:
        raise RuntimeError(f"No release manifests found under s3://{bucket}/{MANIFEST_PREFIX}")
    for key, body, manifest in manifests:
        objects.append((key, body, manifest))
    return sorted(manifests, key=lambda manifest: manifest[0]), sorted(objects, key=lambda item: item[0])


def get_object_if_exists(s3, bucket, key):
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as error:
        response_error = error.response.get("Error", {})
        code = response_error.get("Code")
        status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if code == "NoSuchBucket":
            raise RuntimeError(f"Destination bucket does not exist: {bucket}") from error
        if code in {"404", "NoSuchKey", "NotFound"} or (code is None and status_code == 404):
            return None
        raise

    try:
        return response["Body"].read()
    finally:
        response["Body"].close()


def manifests_match(left, right):
    return json.dumps(left, sort_keys=True, separators=(",", ":")) == json.dumps(
        right, sort_keys=True, separators=(",", ":")
    )


def preflight_destination(s3, bucket, objects):
    uploads = []
    for key, body, source_object in objects:
        existing_body = get_object_if_exists(s3, bucket, key)
        if existing_body is None:
            uploads.append((key, body))
            continue

        try:
            existing_manifest = json.loads(existing_body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Destination object is not valid JSON: s3://{bucket}/{key}") from error
        if not manifests_match(source_object, existing_manifest):
            raise RuntimeError(f"Destination release object conflicts with source: s3://{bucket}/{key}")
    return uploads


def upload_release_objects(s3, bucket, uploads):
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
            existing_body = get_object_if_exists(s3, bucket, key)
            if existing_body is None or not manifests_match(json.loads(body), json.loads(existing_body)):
                raise RuntimeError(f"Destination release object changed during sync: s3://{bucket}/{key}") from error


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        nargs=2,
        metavar=("PROFILE", "BUCKET"),
        required=True,
        help="Source AWS profile and bucket. Use '-' for the default profile.",
    )
    parser.add_argument(
        "--destination",
        action="append",
        nargs=2,
        metavar=("PROFILE", "BUCKET"),
        required=True,
        help="Destination AWS profile and bucket; repeat for each account. Use '-' for the default profile.",
    )
    parser.add_argument("--region", default=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    parser.add_argument(
        "--apply", action="store_true", help="Upload missing manifests and inventories; default is dry-run."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    source_profile, source_bucket = args.source
    source_bucket = normalize_bucket(source_bucket)
    source_s3 = make_session(None if source_profile == "-" else source_profile, args.region).client("s3")
    manifests, release_objects = load_source_manifests(source_s3, source_bucket)

    destinations = []
    seen_destinations = set()
    for profile, bucket in args.destination:
        normalized_bucket = normalize_bucket(bucket)
        destination_key = (profile, normalized_bucket)
        if destination_key in seen_destinations:
            raise RuntimeError(f"Destination was specified more than once: {profile} {normalized_bucket}")
        seen_destinations.add(destination_key)
        destination_s3 = make_session(None if profile == "-" else profile, args.region).client("s3")
        uploads = preflight_destination(destination_s3, normalized_bucket, release_objects)
        destinations.append((profile, normalized_bucket, destination_s3, uploads))

    manifest_count = len(manifests)
    inventory_count = len(release_objects) - manifest_count
    print(
        f"Found {manifest_count} manifests and {inventory_count} package inventories "
        f"in s3://{source_bucket}/{MANIFEST_PREFIX}"
    )
    for profile, bucket, _destination_s3, uploads in destinations:
        already_present = len(release_objects) - len(uploads)
        print(f"{profile} s3://{bucket}: {len(uploads)} objects to upload, {already_present} already match")

    if not args.apply:
        print("Dry run: no destination objects were changed. Pass --apply to upload missing release objects.")
        return

    for _profile, bucket, destination_s3, uploads in destinations:
        upload_release_objects(destination_s3, bucket, uploads)
    print("Release metadata sync complete.")


if __name__ == "__main__":
    main()