from dagster import (
    asset, 
    Definitions, 
    ConfigurableResource, 
    OpExecutionContext, 
    AssetIn
)

@asset
def ImageSample(context: OpExecutionContext) -> str:
    # reading from image path
    img_path = "data/20240109_155650751.jpg"
    context.log.info(f"ImageSample is running, reading new element {img_path}")

    

    return img_path


@asset
def ImageArea(context: OpExecutionContext) -> str:
    # reading from image path
    img_path = "data/20240109_155650751.jpg"
    context.log.info(f"ImageSample is running, reading new element {img_path}")

    return ""

