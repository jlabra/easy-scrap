from typing import Dict
from dagster import (
    AssetExecutionContext,
    asset, 
    sensor,
    Definitions, 
    ConfigurableResource, 
    OpExecutionContext, 
    AssetIn,
    SensorEvaluationContext,
    SensorResult,
    AssetMaterialization,
    MetadataValue
)

from ..resources import constants
import json 

from dagster_aws.s3 import S3Resource

from datetime import datetime as dt

@asset
def cameras_configs(context:AssetExecutionContext, s3:S3Resource) -> Dict:
    context.log.info("materialising cameras_configs")
    
    s3cli = s3.get_client()
    obj_body = s3cli.get_object(Bucket="easyscraptracker", Key="est_elecmetal/cameras_configs.json").get("Body")
    
    camera_configs = json.load(obj_body)

    context.add_output_metadata(
        {
            "preview": MetadataValue.json(camera_configs)
        }
    )
    return camera_configs


