from dagster import asset, Definitions, ConfigurableResource
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor

import logging as logger
logger.basicConfig(
    level=logger.INFO,  # Set the logging level to INFO
    format='%(asctime)s - %(levelname)s - %(message)s')  # Define the log message format


@asset
def ImageSample() -> str:
    print("ImageSample")
    img_path = "data/20240109_155650751.jpg"

    pass
