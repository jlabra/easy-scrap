import boto3
import cv2
import os
from datetime import datetime as dt
from io import BytesIO

# Configure logging
import logging as logger
logger.basicConfig(
    level=logger.INFO,  # Set the logging level to INFO
    format='%(asctime)s - %(levelname)s - %(message)s')  # Define the log message format

# read environment variables
from dotenv import load_dotenv
load_dotenv(override=True)


def main():

    image = cv2.imread("./sample_image.jpg")

    user   = "est_elecmetal"
    camera = "camera_9E06326PAJEE7AC"
    bucket = os.environ["S3_BUCKET"]

    s3 = boto3.client('s3', 
                      aws_access_key_id=os.environ["S3_ACCESS_KEY"],
                      aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
                      region_name=os.environ["S3_REGION"])
    
    ts = dt.utcnow()
    sample_file_path = ts.strftime("%Y-%m-%d/pic_001/%H.%M.%S[R][0@0][0][0].jpg")
    object_key = f"{user}/{camera}/{sample_file_path}"

    img = cv2.imread("./sample_image.jpg")
    
    print(f"[{str(ts)}] - Upload to {object_key}")

    is_success, buffer = cv2.imencode('.jpg', img)
    io_buf = BytesIO(buffer)
    s3.upload_fileobj(io_buf, bucket, object_key, ExtraArgs={'ContentType':'image/jpeg'})
    
    pass

if __name__ == "__main__":
    main()