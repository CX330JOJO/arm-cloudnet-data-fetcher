"""
ARM & CloudNet Data Fetcher
A Python toolkit for automatic download of global ARM and CloudNet
cloud radar and vertical observation data.
"""

__version__ = "0.1.0"
__author__ = "ARM-CloudNet Data Fetcher"

from .arm_fetcher import ARMFetcher
from .cloudnet_fetcher import CloudNetFetcher
from .catalog import DataCatalog
from .config import Config

__all__ = ["ARMFetcher", "CloudNetFetcher", "DataCatalog", "Config"]
