"""Example: Fetch ARM Ka-band radar data for North Slope Alaska."""

from arm_cloudnet_fetcher import ARMFetcher


def main():
    # Initialize fetcher (token from env or config.yaml)
    fetcher = ARMFetcher()

    # List available datastreams for a site
    print("Listing datastreams for NSA...")
    datastreams = fetcher.list_datastreams(site="nsa")
    for ds in datastreams[:5]:
        print(f"  - {ds.get('datastreamId')}: {ds.get('instrumentName', 'N/A')}")

    # Fetch a specific datastream
    print("\nFetching nsakazr2C1.a0 for 2023-01-01 to 2023-01-03...")
    files = fetcher.fetch(
        datastream="nsakazr2C1.a0",
        start_date="2023-01-01",
        end_date="2023-01-03",
    )
    print(f"Downloaded {len(files)} files.")
    for f in files:
        print(f"  - {f}")

    # Fetch all cloud products for a site
    print("\nFetching all cloud products for NSA...")
    results = fetcher.fetch_cloud_products(
        site="nsa",
        start_date="2023-01-01",
        end_date="2023-01-03",
    )
    for ds, paths in results.items():
        print(f"  {ds}: {len(paths)} files")


if __name__ == "__main__":
    main()
