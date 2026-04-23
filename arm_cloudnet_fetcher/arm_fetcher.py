"""ARM (Atmospheric Radiation Measurement) data fetcher.

Supports downloading cloud radar, lidar, microwave radiometer,
and other vertical observation data from ARM Data Center.

API Documentation: https://adc.arm.gov/armlive/
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode

import requests

from .config import Config
from .utils import retry_on_failure, setup_logging, validate_date_range


class ARMFetcher:
    """Fetcher for ARM atmospheric observation data.

    You need a valid ARM Data Center token to access restricted data.
    Apply for a token at: https://adc.arm.gov/armlive/livedata/home
    """

    # ARM facility and site mappings (commonly used)
    COMMON_SITES = {
        "nsa": "North Slope Alaska",
        "sgp": "Southern Great Plains",
        "ena": "Eastern North Atlantic",
        "twpc1": "Tropical Western Pacific Manus",
        "twpc2": "Tropical Western Pacific Nauru",
        "twpc3": "Tropical Western Pacific Darwin",
        "oliktok": "Oliktok Point",
    }

    # Cloud-relevant data streams
    CLOUD_DATASTREAMS = [
        "arsclkazr1kollias",  # Ka-band ARM Zenith Radar
        "arsclwipap",         # Active Remote Sensing of Clouds
        "kazr2",              # Ka-band Zenith Radar
        "mwrlos",             # Microwave Radiometer
        "ceil",               # Ceilometer
        "dlfpt",              # Doppler Lidar
        "rl",                 # Raman Lidar
        "hsrl",               # High Spectral Resolution Lidar
    ]

    def __init__(self, config: Optional[Config] = None, token: Optional[str] = None):
        self.cfg = config or Config()
        self.token = token or self.cfg.get("arm", "token")
        self.base_url = self.cfg.get("arm", "base_url")
        self.output_dir = Path(self.cfg.get("arm", "output_dir"))
        self.timeout = self.cfg.get("arm", "timeout")
        self.retry_times = self.cfg.get("arm", "retry_times")
        self.logger = setup_logging(
            self.cfg.get("logging", "level"),
            self.cfg.get("logging", "format"),
        )
        if not self.token:
            self.logger.warning(
                "No ARM token provided. Some data may be inaccessible. "
                "Get a token at https://adc.arm.gov/armlive/livedata/home"
            )

    @retry_on_failure(max_retries=3, delay=2.0)
    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """Make an authenticated GET request to ARM API."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def list_datastreams(
        self,
        site: Optional[str] = None,
        instrument: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List available datastreams with optional filtering.

        Args:
            site: ARM site code, e.g. 'nsa', 'sgp'.
            instrument: Instrument class, e.g. 'kazr', 'mwrlos'.

        Returns:
            List of datastream metadata dictionaries.
        """
        params = {"type": "datastreams"}
        if site:
            params["site"] = site.lower()
        if instrument:
            params["instrument"] = instrument.lower()
        result = self._request("", params=params)
        return result if isinstance(result, list) else []

    def list_files(
        self,
        datastream: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, str]]:
        """List files available for a given datastream and date range.

        Args:
            datastream: Full ARM datastream name, e.g. 'nsakazr2C1.a0'.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            List of file metadata with 'filename' and 'url' keys.
        """
        start_date, end_date = validate_date_range(start_date, end_date)
        params = {
            "type": "files",
            "datastream": datastream,
            "start": start_date,
            "end": end_date,
        }
        result = self._request("", params=params)
        files = result if isinstance(result, list) else []
        self.logger.info(
            "Found %d files for %s between %s and %s",
            len(files), datastream, start_date, end_date,
        )
        return files

    @retry_on_failure(max_retries=3, delay=2.0)
    def download_file(self, file_url: str, filename: Optional[str] = None) -> Path:
        """Download a single file from ARM archive.

        Args:
            file_url: Direct download URL for the file.
            filename: Optional local filename; derived from URL if omitted.

        Returns:
            Path to the downloaded file.
        """
        if not filename:
            filename = file_url.split("/")[-1]
        local_path = self.output_dir / filename
        local_path.parent.mkdir(parents=True, exist_ok=True)

        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        with requests.get(
            file_url, headers=headers, stream=True, timeout=self.timeout
        ) as resp:
            resp.raise_for_status()
            total_size = int(resp.headers.get("content-length", 0))
            with open(local_path, "wb") as f:
                downloaded = 0
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = downloaded / total_size * 100
                        self.logger.debug("%s: %.1f%%", filename, pct)

        self.logger.info("Downloaded: %s", local_path)
        return local_path

    def fetch(
        self,
        datastream: str,
        start_date: str,
        end_date: str,
        output_dir: Optional[str] = None,
    ) -> List[Path]:
        """Fetch all files for a datastream across a date range.

        Args:
            datastream: ARM datastream identifier.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            output_dir: Override default output directory.

        Returns:
            List of downloaded file paths.
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        files = self.list_files(datastream, start_date, end_date)
        downloaded: List[Path] = []
        for meta in files:
            url = meta.get("url") or meta.get("file")
            name = meta.get("filename") or url.split("/")[-1]
            if not url:
                self.logger.warning("Skipping entry with no URL: %s", meta)
                continue
            try:
                path = self.download_file(url, name)
                downloaded.append(path)
            except Exception as exc:
                self.logger.error("Failed to download %s: %s", name, exc)
        return downloaded

    def fetch_cloud_products(
        self,
        site: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, List[Path]]:
        """Convenience method to fetch common cloud-radar products for a site.

        Args:
            site: ARM site code.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            Mapping from datastream name to list of downloaded paths.
        """
        results: Dict[str, List[Path]] = {}
        for ds in self.CLOUD_DATASTREAMS:
            full_ds = f"{site}{ds}C1.a0"
            try:
                paths = self.fetch(full_ds, start_date, end_date)
                if paths:
                    results[full_ds] = paths
            except Exception as exc:
                self.logger.warning("No data or error for %s: %s", full_ds, exc)
        return results
