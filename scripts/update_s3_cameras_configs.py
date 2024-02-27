import boto3
import os
from datetime import datetime as dt
import argparse
from botocore.exceptions import ClientError
from os import path

# Configure logging
import logging as logger
logger.basicConfig(
    level=logger.INFO,  # Set the logging level to INFO
    format='%(asctime)s - %(levelname)s - %(message)s')  # Define the log message format

# read environment variables
from dotenv import load_dotenv
load_dotenv(override=True)


def main(user):

    bucket = os.environ["S3_BUCKET"]

    s3 = boto3.client('s3', 
                      aws_access_key_id=os.environ["S3_ACCESS_KEY"],
                      aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
                      region_name=os.environ["S3_REGION"])

    object_key = f"{user}/cameras_configs.json"

    print(f"[{str(dt.utcnow())}] - Upload to {object_key}")
    
    try:
        filename = path.join(path.dirname(__file__),"cameras_configs.json")
        print("sending:", filename)
        response = s3.upload_file(filename, bucket, object_key)
    except ClientError as e:
        logger.error(e)
        return False
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", required=True, type=str)
    #parser.add_argument("--camera", required=True, type=str)
    cmd_args = parser.parse_args()
    main(cmd_args.user)

# example python update_s3_camera_configs.py --user est_elecmetal --camera camera_9E06326PAJEE7AC 