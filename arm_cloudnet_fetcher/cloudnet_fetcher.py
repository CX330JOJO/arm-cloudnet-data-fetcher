"""CloudNet data fetcher.

Supports downloading cloud radar, lidar, and classification data
from the ACTRIS CloudNet data portal.

API Documentation: https://cloudnet.fmi.fi/api
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests

from .config import Config
from .utils import retry_on_failure, setup_logging, validate_date_range


class CloudNetFetcher:
    """Fetcher for CloudNet vertical-profile data.

    CloudNet provides standardized cloud-radar, lidar, microwave-radiometer,
    and model data from multiple global sites.
    """

    # Known CloudNet sites (name -> site code)
    COMMON_SITES = {
        "bucharest": "bucharest",
        "granada": "granada",
        "hyytiala": "hyytiala",
        "juelich": "juelich",
        "leipzig": "leipzig",
        "limassol": "limassol",
        "mace-head": "mace-head",
        "norunda": "norunda",
        "ny-alesund": "ny-alesund",
        "potenza": "potenza",
        "palaiseau": "palaiseau",
        "schneefernerhaus": "schneefernerhaus",
    }

    # Standard CloudNet product types
    PRODUCTS = [
        "radar",           # Cloud radar reflectivity
        "lidar",           # Lidar backscatter
        "mwr",             # Microwave radiometer
        "classification",  # Target classification
        "categorize",      # Combined categorization
        "model",           # Model data
        "drizzle",         # Drizzle properties
        "iwc",             # Ice water content
        "lwc",             # Liquid water content
    ]

    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config()
        self.base_url = self.cfg.get("cloudnet", "base_url")
        self.output_dir = Path(self.cfg.get("cloudnet", "output_dir"))
        self.timeout = self.cfg.get("cloudnet", "timeout")
        self.retry_times = self.cfg.get("cloudnet", "retry_times")
        self.logger = setup_logging(
            self.cfg.get("logging", "level"),
            self.cfg.get("logging", "format"),
        )

    @retry_on_failure(max_retries=3, delay=2.0)
    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a GET request to CloudNet API."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Accept": "application/json"}
        resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def list_sites(self) -> List[Dict[str, Any]]:
        """List all available CloudNet measurement sites.

        Returns:
            List of site metadata including id, name, latitude, longitude,
            and measurement period.
        """
        return self._request("sites")

    def list_products(self) -> List[Dict[str, Any]]:
        """List all available CloudNet product types.

        Returns:
            List of product metadata dictionaries.
        """
        return self._request("products")

    def list_files(
        self,
        site: str,
        date: Optional[str] = None,
        product: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List files available for a site, optionally filtered by date or product.

        Args:
            site: CloudNet site code.
            date: Specific date in YYYY-MM-DD format (optional).
            product: Product type, e.g. 'radar', 'classification' (optional).

        Returns:
            List of file metadata dictionaries.
        """
        params: Dict[str, str] = {"site": site}
        if date:
            params["date"] = date
        if product:
            params["product"] = product
        return self._request("files", params=params)

    @retry_on_failure(max_retries=3, delay=2.0)
    def download_file(self, file_uuid: str, filename: Optional[str] = None) -> Path:
        """Download a single file by its CloudNet UUID.

        Args:
            file_uuid: CloudNet file UUID.
            filename: Optional local filename.

        Returns:
            Path to the downloaded file.
        """
        url = f"{self.base_url}/download/{file_uuid}"
        if not filename:
            filename = f"{file_uuid}.nc"
        local_path = self.output_dir / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)

        with requests.get(url, stream=True, timeout=self.timeout) as resp:
            resp.raise_for_status()
            # Try to get filename from Content-Disposition header
            cd = resp.headers.get("content-disposition", "")
            if "filename=" in cd:
                fname = cd.split("filename=")[-1].strip('"')
                local_path = local_path.parent / fname
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

        self.logger.info("Downloaded: %s", local_path)
        return local_path

    def fetch(
        self,
        site: str,
        start_date: str,
        end_date: str,
        product: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> List[Path]:
        """Fetch all CloudNet files for a site across a date range.

        Args:
            site: CloudNet site code.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            product: Optional product type filter.
            output_dir: Override default output directory.

        Returns:
            List of downloaded file paths.
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        start_date, end_date = validate_date_range(start_date, end_date)
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        downloaded: List[Path] = []
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            try:
                files = self.list_files(site, date=date_str, product=product)
                for meta in files:
                    uuid = meta.get("uuid")
                    fname = meta.get("filename")
                    if not uuid:
                        continue
                    try:
                        path = self.download_file(uuid, fname)
                        downloaded.append(path)
                    except Exception as exc:
                        self.logger.error("Failed to download %s: %s", uuid, exc)
            except Exception as exc:
                self.logger.warning("Error listing files for %s: %s", date_str, exc)
            current += __import__("datetime").timedelta(days=1)

        self.logger.info(
            "Downloaded %d files for %s between %s and %s",
            len(downloaded), site, start_date, end_date,
        )
        return downloaded

    def fetch_products(
        self,
        site: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, List[Path]]:
        """Convenience method to fetch all standard products for a site.

        Args:
            site: CloudNet site code.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            Mapping from product name to list of downloaded paths.
        """
        results: Dict[str, List[Path]] = {}
        for prod in self.PRODUCTS:
            try:
                paths = self.fetch(site, start_date, end_date, product=prod)
                if paths:
                    results[prod] = paths
            except Exception as exc:
                self.logger.warning("No data or error for %s/%s: %s", site, prod, exc)
        return results
