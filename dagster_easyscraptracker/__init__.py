from importlib import resources
from dagster import Definitions, load_assets_from_modules

from .assets import granulometry

granulometry_assets = load_assets_from_modules([granulometry])

defs = Definitions(
    assets=[
        *granulometry_assets,
    ],
    resources=[

    ]
)
