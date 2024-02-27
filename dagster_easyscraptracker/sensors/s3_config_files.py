import os
from datetime import datetime as dt

from dagster_aws.s3 import S3Resource
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
    AssetMaterialization
)



def utc_now_str() -> str:
    return dt.utcnow().strftime("%Y-%m-%d, %H:%M:%S")



@sensor()
def cameras_configs_sensor(
    context: SensorEvaluationContext,
    s3:S3Resource) -> SensorResult:
    
    since_date = context.cursor or None
    
    s3_cli = s3.get_client()

    response = s3_cli.head_object(
        Bucket=os.environ["S3_BUCKET"], 
        Key=f"{os.environ['APP_USER']}/cameras_configs.json")
    
    last_modified = str(response['LastModified'])

    context.log.info(f"{since_date} == {str(last_modified)}?")

    if since_date == last_modified:
        context.log.info(f"UPTODATE - There is no update for cameras_configs.json last modified {last_modified} since_date:{since_date}")
        return None
    else:
        # Materialization happened in external system, but is recorded here
        context.log.info(f"UPDATING asset camera configs")
        
        context.update_cursor(str(last_modified))

        
        return SensorResult(
            asset_events=[
                AssetMaterialization(
                    asset_key="cameras_configs",
                    metadata={
                        "source": f'From sensor "{context.sensor_name}" at UTC time "{utc_now_str()}"'
                    },
                )
            ]
        )



    