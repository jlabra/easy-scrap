from importlib import resources
from dagster import Definitions, load_assets_from_modules
from dagster_aws.s3 import S3Resource
import os
from .assets import granulometry

#sensors & jobs
from .jobs.process_image import process_image_job
from .sensors.s3_bucket_file import bucket_sensor

granulometry_assets = load_assets_from_modules([granulometry])

defs = Definitions(
    assets=[
        *granulometry_assets,
    ],
    sensors=[
        bucket_sensor
    ],
    jobs=[
        process_image_job
    ],

    resources={
        "s3": S3Resource(
            aws_access_key_id=os.environ["S3_ACCESS_KEY"],
            aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
            region_name=os.environ["S3_REGION"]
            )
    }
)
