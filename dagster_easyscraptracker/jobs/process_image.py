import re

from dagster import (   
        op, 
        job, 
        Config,
        MetadataValue,
        OpExecutionContext        
)


class S3FileConfig(Config):
    s3_key: str

@op
def segmenting_image(context:OpExecutionContext, config: S3FileConfig):
    context.log.info(f"segmenting image from s3: {config.s3_key}")
    user, camera_id, date, _, filename = config.s3_key.split("/")
    year, month, day = [int(part) for part in date.split("-")] 
    hour, min, sec = [int(part) for part in re.sub(r'\[.*', '', filename).split(".")] 
    
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
    #metadata = {"preview": MetadataValue.json(data)}
    #context.add_output_metadata(metadata=metadata)
    return data


@job
def process_image_job():
    data = segmenting_image()



