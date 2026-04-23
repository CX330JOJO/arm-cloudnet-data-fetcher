"""Command-line interface for ARM and CloudNet fetchers."""

import argparse
import sys
from pathlib import Path

from .arm_fetcher import ARMFetcher
from .cloudnet_fetcher import CloudNetFetcher
from .config import Config


def arm_main():
    parser = argparse.ArgumentParser(description="Fetch ARM data")
    parser.add_argument("--datastream", required=True, help="ARM datastream name")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--token", help="ARM API token")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--config", "-c", help="Path to config.yaml")
    args = parser.parse_args()

    cfg = Config(args.config) if args.config else None
    fetcher = ARMFetcher(config=cfg, token=args.token)
    if args.output:
        fetcher.output_dir = Path(args.output)

    files = fetcher.fetch(args.datastream, args.start, args.end)
    print(f"Downloaded {len(files)} files.")
    return 0


def cloudnet_main():
    parser = argparse.ArgumentParser(description="Fetch CloudNet data")
    parser.add_argument("--site", required=True, help="CloudNet site code")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--product", help="Product type (radar, lidar, etc.)")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--config", "-c", help="Path to config.yaml")
    args = parser.parse_args()

    cfg = Config(args.config) if args.config else None
    fetcher = CloudNetFetcher(config=cfg)
    if args.output:
        fetcher.output_dir = Path(args.output)

    files = fetcher.fetch(args.site, args.start, args.end, product=args.product)
    print(f"Downloaded {len(files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(arm_main())
