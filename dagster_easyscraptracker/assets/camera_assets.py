from dagster import asset, Definitions, ConfigurableResource, OpExecutionContext, AssetIn
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor

import logging as logger
logger.basicConfig(
    level=logger.INFO,  # Set the logging level to INFO
    format='%(asctime)s - %(levelname)s - %(message)s')  # Define the log message format




@asset
def ImageSample(context: OpExecutionContext) -> str:
    # reading from image path
    img_path = "data/20240109_155650751.jpg"
    context.log.info(f"ImageSample is running, reading new element {img_path}")

    

    return image_folder


@asset
def ImageArea(ctx: OpExecutionContext) -> str:
    # reading from image path
    img_path = "data/20240109_155650751.jpg"
    ctx.log.info(f"ImageSample is running, reading new element {img_path}")

    return ""

@asset(ins={"elements_folder": AssetIn("ImageSample")})
def ElementsFolder(context: OpExecutionContext, deps=[ImageSample])->str:

    return ""