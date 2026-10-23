"""a module to hold some common configuration items that various scripts may need"""
import os

from botocore.config import Config

# we need some mitigation of potential API rate restrictions for the (especially) Batch API
retry_config = Config(retries={"max_attempts": 20, "mode": "standard"})


def get_env() -> str:
    """Return the configured Calcloud environment suffix, or an empty string."""
    return os.environ.get("CALCLOUD_ENVIRONMENT", "")
