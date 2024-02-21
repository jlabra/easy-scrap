import os

from dagster import (   
    sensor,
    RunRequest, 
    RunConfig,
    SensorEvaluationContext,
    SkipReason,
    ConfigurableResource
)

from dagster_aws.s3 import S3Resource

from dagster_aws.s3.sensor import get_s3_keys

# custom 
from ..jobs.process_image import S3FileConfig, process_image_job

@sensor(job=process_image_job)
def bucket_sensor(context: SensorEvaluationContext, s3: S3Resource):
    context.log.info(f"bucket_sensor - requesting job process image for new keys")
    
    s3_session = s3.get_client()
    since_key = context.cursor or None
    
    new_s3_keys = get_s3_keys(bucket=os.environ["S3_BUCKET"], 
                              s3_session=s3_session,
                              since_key=since_key)
    
    if not new_s3_keys:
        context.log.info(f"bucket_sensor - There is no new s3 files")
        return SkipReason("No new s3 files found for bucket my_s3_bucket.")
    else:
        last_key = new_s3_keys[-1]
        for s3_key in new_s3_keys:
            yield RunRequest(run_key=s3_key, run_config=RunConfig(ops={"segmenting_image": S3FileConfig(s3_key=s3_key)}))
        
        context.update_cursor(last_key)
