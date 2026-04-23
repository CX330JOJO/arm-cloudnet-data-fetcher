"""Example: Fetch CloudNet radar data from Hyytiala site."""

from arm_cloudnet_fetcher import CloudNetFetcher


def main():
    # Initialize fetcher
    fetcher = CloudNetFetcher()

    # List available sites
    print("Listing CloudNet sites...")
    sites = fetcher.list_sites()
    for site in sites[:5]:
        print(f"  - {site.get('id')}: {site.get('humanReadableName', 'N/A')}")

    # Fetch radar product for a specific site and date range
    print("\nFetching radar data from hyytiala for 2023-06-01 to 2023-06-03...")
    files = fetcher.fetch(
        site="hyytiala",
        start_date="2023-06-01",
        end_date="2023-06-03",
        product="radar",
    )
    print(f"Downloaded {len(files)} files.")
    for f in files:
        print(f"  - {f}")

    # Fetch all standard products for a site
    print("\nFetching all products from hyytiala...")
    results = fetcher.fetch_products(
        site="hyytiala",
        start_date="2023-06-01",
        end_date="2023-06-03",
    )
    for prod, paths in results.items():
        print(f"  {prod}: {len(paths)} files")


if __name__ == "__main__":
    main()
