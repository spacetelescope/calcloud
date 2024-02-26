""" a module to hold some common configuration items that various scripts may need """

from botocore.config import Config

# we need some mitigation of potential API rate restrictions for the (especially) Batch API
retry_config = Config(retries={"max_attempts": 20, "mode": "standard"})
