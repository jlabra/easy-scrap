import re
import copy
import json 
import cv2
import numpy as np
import os
from io import BytesIO

from typing import Tuple, Dict

from dagster import (   
        op, 
        job, 
        in_process_executor,
        Config,
        MetadataValue,
        OpExecutionContext,
        In        
)

from ..resources import constants
from dagster_aws.s3 import S3Resource

# custom librarys
import torch
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor


class S3FileConfig(Config):
    s3_key: str

@op
def store_on_dynamo():
    pass


def getSamPredictor():
    DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    MODEL_TYPE = "vit_h"
    CHECKPOINT_PATH  = os.environ["SAM_PATH"]
    sam = sam_model_registry[MODEL_TYPE](checkpoint=CHECKPOINT_PATH)
    sam.to(device=DEVICE)
    mask_predictor = SamPredictor(sam)
    return mask_predictor


def numpy_to_list(np_array):
    return np_array.tolist()

# filter masks by min/max area
def filter_masks_by_area(masks, min_area=0, max_area=20000):
    return [ mask for mask in masks if min_area<= mask["area"] <= max_area ]

def get_masks_image(masks, input_image):
    if len(masks) == 0:
        return
    
    sorted_anns = sorted(masks, key=(lambda x: x['area'] ), reverse=True)

    # create a image with same shape of input image
    img = np.ones((input_image.shape[0], input_image.shape[1], 4), dtype=np.uint8)
    img[:, :, 3] = 0  # Inicializar el canal alfa en cero
    
    for ann in sorted_anns:
        m = ann['segmentation']
        color_mask = np.concatenate([np.random.randint(0, 255, 3), [90]])  # Color aleatorio con opacidad 0.35
        img[m] = color_mask

    # convert input image to  RGBA (adding alpha channel)
    input_image_rgba = cv2.cvtColor(input_image, cv2.COLOR_BGR2BGRA)

    # overlay generated image to input image
    output_image = cv2.addWeighted(input_image_rgba, 0.5, img, 0.5, 0)

    # convert output image to BGR (delete alfa channel)
    output_image = cv2.cvtColor(output_image, cv2.COLOR_BGRA2BGR)

    return output_image

@op
def read_incomming_image(context:OpExecutionContext, 
               s3:S3Resource, 
               config: S3FileConfig) -> Tuple:
    
    '''Return image, camera configuration and image data'''

    context.log.info(f"reading image from s3: {config.s3_key}")
    user, camera_id, date, _, filename = config.s3_key.split("/")

    ## get last config file from s3 ( all cameras )
    s3cli = s3.get_client()
    obj_body = s3cli.get_object(Bucket="easyscraptracker", Key=f"{user}/cameras_configs.json").get("Body")
    configurations = json.load(obj_body)

    # this image is in BGR Format (opencv)
    s3_obj = s3cli.get_object(Bucket="easyscraptracker", Key=config.s3_key)
    image_bytes = s3_obj.get("Body").read() 
    image = cv2.imdecode(np.asarray(bytearray(image_bytes), dtype="uint8"), cv2.IMREAD_COLOR)

    date, time = str(s3_obj["LastModified"]).split(" ")
    year, month, day = [int(part) for part in date.split("-")] 
    hour, min, sec  =  [int(part) for part in time.split("+")[0].split(":")] 
    
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
    
    # getting config for current camera
    camera_config = configurations["cameras"][camera_id]

    context.log.info(f"segmenting image from s3: {config.s3_key}")
    context.log.info(f"config from {camera_id}: {camera_config}")

    return (image, camera_config, data)

@op
def segmenting_base_image(context: OpExecutionContext, upstream: tuple) -> Tuple:
    '''Return the cropped region of interest based on camera segmentation box'''
    image, camera_config, data = upstream

    context.log.info(f"segmenting_image - camera_config: {camera_config}")
    context.log.info(f"segmenting_image - data: {data}")

    # FIRST SEGMENT by box using sampredictor ----------------------------------------------------------------
    DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    MODEL_TYPE = "vit_h"
    CHECKPOINT_PATH  = os.environ["SAM_PATH"]
    sam = sam_model_registry[MODEL_TYPE](checkpoint=CHECKPOINT_PATH)
    sam.to(device=DEVICE)
    mask_predictor = SamPredictor(sam)

    # getting segmentation base box from configuration 
    sbox = camera_config["segment_base_box"]
    x, y, w, h = sbox["x"], sbox["y"], sbox["w"], sbox["h"]

    # setting image to sam predictor
    mask_predictor.set_image(image)
    context.log.info(f"segmenting_image - mask_predictor setting image...")

    # getting segmented object results for camera segmentation base box
    masks, scores, logits = mask_predictor.predict(box=np.array([x, y, (x+w), (y+h)]), multimask_output=False)

    result = image*np.transpose(masks, (1, 2, 0))
    
    # segmented cropped image
    cropped_result = result[y:y+h, x:x+w]

    # segmented cropped image
    cropped_image= image[y:y+h, x:x+w]

    data["segment_base_box"] = camera_config["segment_base_box"]

    return cropped_image, cropped_result, data




@op
def segmenting_anything(context: OpExecutionContext, 
                        upstream: tuple):
    
    ''' Return a set of N masks from sam algorith '''

    cropped_image, cropped_result, data = upstream

    # pass sam model to resource, or asset
    DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    MODEL_TYPE = "vit_h"
    CHECKPOINT_PATH  = os.environ["SAM_PATH"]
    sam = sam_model_registry[MODEL_TYPE](checkpoint=CHECKPOINT_PATH)
    sam.to(device=DEVICE)

    mask_generator = SamAutomaticMaskGenerator(
        model=sam,
        points_per_side=32,
        pred_iou_thresh=0.86,
        stability_score_thresh=0.92,
        crop_n_layers=1,
        crop_n_points_downscale_factor=2,
        min_mask_region_area=100,  # Requires open-cv to run post-processing
    )

    # detected elements: 
    masks = mask_generator.generate(cropped_result)
    filtered_masks = filter_masks_by_area(masks, min_area=0, max_area=20000)
    # filter masks by area size
    data["masks"] = filtered_masks

    cropped_result_masked = get_masks_image(filtered_masks, cropped_result)

    return cropped_image, cropped_result, cropped_result_masked, data

@op
def upload_to_s3(context: OpExecutionContext, 
                 s3:S3Resource, 
                 upstream: tuple):
    
    '''Upload all files from processing job to amazon S3 '''

    s3cli = s3.get_client()

    cropped_image, cropped_result, cropped_result_masked, data = upstream
    
    bucket = os.environ["S3_BUCKET"]

    cropped_image_filename = f"cropped_image_{data['filename']}"
    cropped_segmented_image_filename = f"cropped_segmented_image_{data['filename']}"
    cropped_segmented_image_masks_filename = f"cropped_segmented_image_masks_{data['filename']}"

    output_path = "{0}/{1}/{2}/output".format(*data['s3_key'].split('/')[0:3])
    output_path = f"{output_path}/{data['filename']}"
    
    object_key_image = f"{output_path}/{cropped_image_filename}"
    object_key_segmented_image = f"{output_path}/{cropped_segmented_image_filename}"
    object_key_segmented_image_masks = f"{output_path}/{cropped_segmented_image_masks_filename}"

    object_key_data_lite = f"{output_path}/{cropped_image_filename.replace('.jpg','')}_data_lite_.json"
    object_key_data_full = f"{output_path}/{cropped_image_filename.replace('.jpg','')}_data_full_.json"

    data["base_image_key"] = object_key_image
    data["segmented_base_image_key"] = object_key_segmented_image
    data["segmented_base_image_masks_key"] = object_key_segmented_image_masks

    data["data_full"] = object_key_data_full
    data["data_lite"] = object_key_data_lite
    
    datafull = copy.deepcopy(data)
    for i, dm in enumerate(data["masks"]):
        #context.log.info(f"ON FOR: {dm}")
        x, y, w, h = (e for e in dm['bbox'])
        dm['mask_id'] = i
        #dm["segmentation"] = dm["segmentation"][y:(y+h), x:x+w].tolist()
        dm.__delitem__('segmentation')
        datafull['masks'][i]['mask_id'] = i
        datafull['masks'][i]['segmentation'] = datafull['masks'][i]['segmentation'][y:(y+h), x:x+w].tolist()
    
    json_data = json.dumps(data)
    json_data_full = json.dumps(datafull)

    #uploading cropped image
    is_success, img_buffer = cv2.imencode('.jpg', cropped_image)
    s3cli.upload_fileobj(BytesIO(img_buffer), bucket, object_key_image, ExtraArgs={'ContentType':'image/jpeg'})
    is_success, img_buffer = cv2.imencode('.jpg', cropped_result)
    s3cli.upload_fileobj(BytesIO(img_buffer), bucket, object_key_segmented_image, ExtraArgs={'ContentType':'image/jpeg'})
    is_success, img_buffer = cv2.imencode('.jpg', cropped_result_masked)
    s3cli.upload_fileobj(BytesIO(img_buffer), bucket, object_key_segmented_image_masks, ExtraArgs={'ContentType':'image/jpeg'})

    #uploading results file file
    context.log.info(f"uploading data lite version")
    s3cli.put_object(Body=json_data, Bucket=bucket, Key=object_key_data_lite, ContentType='application/json')
    context.log.info(f"uploading data full version")
    s3cli.put_object(Body=json_data_full, Bucket=bucket, Key=object_key_data_full, ContentType='application/json')

#@job #use job only for production 
@job(executor_def=in_process_executor)
def process_image_job():
    upload_to_s3(segmenting_anything(segmenting_base_image(read_incomming_image())))