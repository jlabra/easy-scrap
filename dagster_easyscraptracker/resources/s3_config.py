from dagster import (
    Config,
    ConfigurableResource
    )


class S3Config(Config):
    s3_bucket: str
    s3_prefix: str