import re
import json 

from dagster import (   
        op, 
        job, 
        Config,
        MetadataValue,
        OpExecutionContext        
)
from ..resources import constants

from dagster_aws.s3 import S3Resource


class S3FileConfig(Config):
    s3_key: str

@op
def store_on_dynamo():
    pass

# obtiene solo de s3 si este se actualizo 
def get_camera_config(context, s3:S3Resource):
    s3cli = s3.get_client()
    obj = s3.Object(constants.S3_BUCKET, f"{constants.APP_USER}/cameras_configs.json")
    
    context.log.info(f"getCameraConfig : {obj} {type(obj)}")

    pass

@op
def segmenting_image(context:OpExecutionContext, s3:S3Resource, config: S3FileConfig):
    context.log.info(f"segmenting image from s3: {config.s3_key}")
    user, camera_id, date, _, filename = config.s3_key.split("/")
    year, month, day = [int(part) for part in date.split("-")] 
    hour, min, sec = [int(part) for part in re.sub(r'\[.*', '', filename).split(".")] 
    
    # get last config file from s3 ( all cameras )
    s3cli = s3.get_client()
    obj_body = s3cli.get_object(Bucket="easyscraptracker", Key="est_elecmetal/cameras_configs.json").get("Body")
    configurations = json.load(obj_body)

    camera_config = configurations["cameras"][camera_id]

    data = {
        "year": year,
        "month": month,
        "day": day,
        "hour":hour, 
        "min":min,
        "sec":sec,
        "user": user, 
        "camera_id": camera_id,
        "filename": filename,
        "s3_key": config.s3_key
    }
    
    context.log.info(f"segmenting image from s3: {config.s3_key}")
    context.log.info(f"config from {camera_id}: {camera_config}")


    #metadata = {"preview": MetadataValue.json(data)}
    #context.add_output_metadata(metadata=metadata)
    return data


@job
def process_image_job():
    data = segmenting_image()



