from dagster_aws.s3 import s3_pickle_io_manager, s3_resource

from .api_resource import ApiResource

RESOURCES_LOCAL = {
    "io_manager": s3_pickle_io_manager,
    "s3": s3_resource,
    "easyscraptracker_client": ApiResource(
        host="easyscraptracker.ninja", 
        protocol="https", 
        endpoint="images")
}

RESOURCES_STAGING = {
    "io_manager": s3_pickle_io_manager,
    "s3": s3_resource,
    "easyscraptracker_client": ApiResource(
        host="easyscraptracker.ninja", 
        protocol="https", 
        endpoint="images")
}

RESOURCES_PROD = {
    "io_manager": s3_pickle_io_manager,
    "s3": s3_resource,
    "easyscraptracker_client": ApiResource(
        host="easyscraptracker.ninja", 
        protocol="https", 
        endpoint="images")
}