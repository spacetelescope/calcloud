import json
import os

from calcloud.log import configure_logging

logger = configure_logging()


def _log_level(build_status):
    status = (build_status or "UNKNOWN").upper()
    if status in {"FAILED", "FAULT", "STOPPED", "TIMED_OUT"}:
        return "ERROR"
    if status in {"SUCCEEDED", "COMPLETED", "IN_PROGRESS", "QUEUED", "PENDING"}:
        return "INFO"
    return "WARNING"


def lambda_handler(event, context):
    logger.info("Received CodeBuild EventBridge event: %s", event)

    detail = event.get("detail") or {}
    if not detail:
        logger.warning("CodeBuild event missing detail payload")
        return {"statusCode": 400, "body": "missing detail"}

    build_status = detail.get("build-status") or "UNKNOWN"
    payload = {
        "source": "aws.codebuild",
        "project_name": detail.get("project-name") or "unknown",
        "build_id": detail.get("build-id") or "unknown",
        "build_status": build_status,
        "level": _log_level(build_status),
        "detail": detail,
        "environment": os.environ.get("aws_env", "unknown"),
    }

    if payload["level"] == "ERROR":
        logger.error(json.dumps(payload, default=str))
    else:
        logger.info(json.dumps(payload, default=str))
    return {
        "statusCode": 200,
        "body": "CodeBuild event logged for Datadog CloudWatch integration",
    }
