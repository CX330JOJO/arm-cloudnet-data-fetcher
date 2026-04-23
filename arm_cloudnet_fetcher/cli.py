"""Command-line interface for ARM and CloudNet fetchers."""

import argparse
import sys
from pathlib import Path

from .arm_fetcher import ARMFetcher
from .cloudnet_fetcher import CloudNetFetcher
from .catalog import DataCatalog
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


def catalog_main():
    """CLI entry point for the data catalog / inventory tool."""
    parser = argparse.ArgumentParser(
        description=(
            "Browse ARM & CloudNet data catalog: "
            "find out when, where, and what data is available."
        )
    )
    parser.add_argument(
        "--config", "-c", help="Path to config.yaml (ARM token may be needed)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- sites ---
    p = sub.add_parser("sites", help="List available observation sites")
    p.add_argument(
        "--source",
        choices=["arm", "cloudnet", "all"],
        default="all",
        help="Filter by data source",
    )

    # --- instruments ---
    p = sub.add_parser(
        "instruments", help="List instrument (ARM) or product (CloudNet) types"
    )
    p.add_argument(
        "--source",
        choices=["arm", "cloudnet", "all"],
        default="all",
        help="Filter by data source",
    )

    # --- probe ---
    p = sub.add_parser(
        "probe",
        help="Probe data availability for a site and date range (live API query)",
    )
    p.add_argument(
        "--source", choices=["arm", "cloudnet"], required=True,
        help="Data source to probe"
    )
    p.add_argument("--site", required=True, help="Site code, e.g. nsa or hyytiala")
    p.add_argument(
        "--start", required=True, help="Start date (YYYY-MM-DD)"
    )
    p.add_argument(
        "--end", required=True, help="End date (YYYY-MM-DD)"
    )

    # --- search ---
    p = sub.add_parser("search", help="Search sites by keyword")
    p.add_argument("keyword", help="Keyword to search (case-insensitive)")

    args = parser.parse_args()

    cfg = Config(args.config) if args.config else None
    catalog = DataCatalog(config=cfg)

    if args.command == "sites":
        _cmd_sites(catalog, args.source)
    elif args.command == "instruments":
        _cmd_instruments(catalog, args.source)
    elif args.command == "probe":
        _cmd_probe(catalog, args.source, args.site, args.start, args.end)
    elif args.command == "search":
        _cmd_search(catalog, args.keyword)

    return 0


def _cmd_sites(catalog: DataCatalog, source: str) -> None:
    if source in ("all", "arm"):
        print("\n=== ARM Sites ===")
        sites = catalog.list_arm_sites()
        rows = [[s["code"], s["name"]] for s in sites]
        catalog.print_table(["Code", "Name"], rows)

    if source in ("all", "cloudnet"):
        print("\n=== CloudNet Sites ===")
        sites = catalog.list_cloudnet_sites()
        rows = []
        for s in sites:
            code = s.get("id") or s.get("code", "?")
            name = s.get("name", "?")
            lat = s.get("latitude", "?") or "?"
            lon = s.get("longitude", "?") or "?"
            rows.append([code, name, str(lat), str(lon)])
        catalog.print_table(["Code", "Name", "Latitude", "Longitude"], rows)


def _cmd_instruments(catalog: DataCatalog, source: str) -> None:
    if source in ("all", "arm"):
        print("\n=== ARM Cloud-Relevant Instruments ===")
        insts = catalog.list_arm_instruments()
        rows = [[i["suffix"], i["instrument"]] for i in insts]
        catalog.print_table(["Datastream Suffix", "Instrument"], rows)

    if source in ("all", "cloudnet"):
        print("\n=== CloudNet Products ===")
        prods = catalog.list_cloudnet_products()
        rows = []
        for p in prods:
            pid = p.get("id") or p.get("code", "?")
            name = p.get("name", "?")
            rows.append([pid, name])
        catalog.print_table(["Product ID", "Name"], rows)


def _cmd_probe(
    catalog: DataCatalog,
    source: str,
    site: str,
    start: str,
    end: str,
) -> None:
    print(f"\nProbing {source.upper()} site '{site}' for {start} ~ {end} ...")
    print("(This may take a moment — one API call per instrument/product)\n")

    if source == "arm":
        result = catalog.probe_arm(site, start, end)
        print(f"Site      : {result['site_name']} ({result['site']})")
        print(f"Period    : {result['period']}")
        print(f"\n--- Available Datastreams ({len(result['available_datastreams'])}) ---")
        if result["available_datastreams"]:
            rows = [
                [r["datastream"], r["instrument"], r["files"]]
                for r in result["available_datastreams"]
            ]
            catalog.print_table(["Datastream", "Instrument", "Files"], rows)
        else:
            print("  None")
        if result["unavailable"]:
            print(f"\n--- Not Available ({len(result['unavailable'])}) ---")
            for ds in result["unavailable"]:
                print(f"  - {ds}")

    else:  # cloudnet
        result = catalog.probe_cloudnet(site, start, end)
        print(f"Site      : {result['site']}")
        print(f"Period    : {result['period']}")
        print(f"\n--- Available Products ({len(result['available_products'])}) ---")
        if result["available_products"]:
            rows = [
                [r["product"], r["first_date"], r["files_on_first_date"]]
                for r in result["available_products"]
            ]
            catalog.print_table(["Product", "First Date", "Files"], rows)
        else:
            print("  None")
        if result["unavailable"]:
            print(f"\n--- Not Available ({len(result['unavailable'])}) ---")
            for prod in result["unavailable"]:
                print(f"  - {prod}")


def _cmd_search(catalog: DataCatalog, keyword: str) -> None:
    results = catalog.search_site(keyword)
    total = len(results["arm"]) + len(results["cloudnet"])
    print(f"\nFound {total} site(s) matching '{keyword}':\n")

    if results["arm"]:
        print("=== ARM ===")
        rows = [[r["code"], r["name"]] for r in results["arm"]]
        catalog.print_table(["Code", "Name"], rows)

    if results["cloudnet"]:
        print("\n=== CloudNet ===")
        rows = [[r["code"], r["name"]] for r in results["cloudnet"]]
        catalog.print_table(["Code", "Name"], rows)

    if not total:
        print("  No matches. Try a broader keyword.")


if __name__ == "__main__":
    sys.exit(arm_main())
