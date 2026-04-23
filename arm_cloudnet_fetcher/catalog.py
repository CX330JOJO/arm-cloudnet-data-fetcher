"""Data catalog / inventory for ARM and CloudNet.

Quickly discover:
- **Where** — available observation sites
- **What**  — instrument / product types
- **When**  — data availability for a given date range
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from .arm_fetcher import ARMFetcher
from .cloudnet_fetcher import CloudNetFetcher
from .config import Config
from .utils import setup_logging, validate_date_range


class DataCatalog:
    """Unified catalog for browsing ARM and CloudNet metadata."""

    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config()
        self.arm = ARMFetcher(config=self.cfg)
        self.cloudnet = CloudNetFetcher(config=self.cfg)
        self.logger = setup_logging(
            self.cfg.get("logging", "level"),
            self.cfg.get("logging", "format"),
        )

    # ------------------------------------------------------------------
    # ARM summaries
    # ------------------------------------------------------------------
    def list_arm_sites(self) -> List[Dict[str, str]]:
        """Return ARM site list with codes and names."""
        return [
            {"code": code, "name": name}
            for code, name in self.arm.COMMON_SITES.items()
        ]

    def list_arm_instruments(self) -> List[Dict[str, str]]:
        """Return ARM cloud-relevant instrument types."""
        instruments = []
        for ds in self.arm.CLOUD_DATASTREAMS:
            instruments.append({
                "suffix": ds,
                "instrument": self._instrument_name(ds),
            })
        return instruments

    @staticmethod
    def _instrument_name(ds: str) -> str:
        mapping = {
            "arsclkazr1kollias": "ARSCL + KAZR (Kollias)",
            "arsclwipap": "ARSCL WIPAP",
            "kazr2": "Ka-band Zenith Radar (KAZR)",
            "mwrlos": "Microwave Radiometer (MWRLOS)",
            "ceil": "Ceilometer",
            "dlfpt": "Doppler Lidar (DLFPT)",
            "rl": "Raman Lidar",
            "hsrl": "High Spectral Resolution Lidar",
        }
        return mapping.get(ds, ds)

    def probe_arm(
        self,
        site: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Probe ARM data availability for a site across a date range.

        This method performs live API queries for each known cloud
        datastream at the requested site.  Use a short date range
        (1--3 days) for a quick check.

        Returns:
            Dict with keys: site, site_name, period,
            available_datastreams, unavailable.
        """
        start_date, end_date = validate_date_range(start_date, end_date)
        available: List[Dict[str, Any]] = []
        unavailable: List[str] = []

        for ds in self.arm.CLOUD_DATASTREAMS:
            full_ds = f"{site}{ds}C1.a0"
            try:
                files = self.arm.list_files(full_ds, start_date, end_date)
                if files:
                    available.append({
                        "datastream": full_ds,
                        "files": len(files),
                        "instrument": self._instrument_name(ds),
                    })
                else:
                    unavailable.append(full_ds)
            except Exception as exc:
                self.logger.debug("No data for %s: %s", full_ds, exc)
                unavailable.append(full_ds)

        return {
            "site": site,
            "site_name": self.arm.COMMON_SITES.get(site, site),
            "period": f"{start_date} to {end_date}",
            "available_datastreams": available,
            "unavailable": unavailable,
        }

    # ------------------------------------------------------------------
    # CloudNet summaries
    # ------------------------------------------------------------------
    def list_cloudnet_sites(self) -> List[Dict[str, Any]]:
        """Return CloudNet site list from API or built-in fallback."""
        try:
            sites = self.cloudnet.list_sites()
            if isinstance(sites, list) and sites:
                return sites
        except Exception as exc:
            self.logger.warning("CloudNet API unreachable, using fallback: %s", exc)
        return [
            {"id": k, "name": v, "latitude": None, "longitude": None}
            for k, v in self.cloudnet.COMMON_SITES.items()
        ]

    def list_cloudnet_products(self) -> List[Dict[str, Any]]:
        """Return CloudNet product types from API or built-in fallback."""
        try:
            products = self.cloudnet.list_products()
            if isinstance(products, list) and products:
                return products
        except Exception as exc:
            self.logger.warning("CloudNet API unreachable, using fallback: %s", exc)
        return [{"id": p, "name": p} for p in self.cloudnet.PRODUCTS]

    def probe_cloudnet(
        self,
        site: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Probe CloudNet data availability for a site across a date range.

        This method performs live API queries for each product type.
        Use a short date range (1--3 days) for a quick check.

        Returns:
            Dict with keys: site, period,
            available_products, unavailable.
        """
        start_date, end_date = validate_date_range(start_date, end_date)
        available: List[Dict[str, Any]] = []
        unavailable: List[str] = []

        products = self.cloudnet.PRODUCTS
        # Try to enrich from API
        try:
            api_prods = self.cloudnet.list_products()
            if isinstance(api_prods, list) and api_prods:
                products = [
                    p.get("id", p) for p in api_prods
                    if isinstance(p, dict)
                ]
        except Exception:
            pass

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        found = set()

        # Iterate day-by-day until we find at least one file for each product.
        # This avoids querying every day for products that already have data.
        current = start
        while current <= end and len(found) < len(products):
            date_str = current.strftime("%Y-%m-%d")
            for prod in products:
                if prod in found:
                    continue
                try:
                    files = self.cloudnet.list_files(
                        site, date=date_str, product=prod
                    )
                    if files:
                        found.add(prod)
                        available.append({
                            "product": prod,
                            "first_date": date_str,
                            "files_on_first_date": len(files),
                        })
                except Exception as exc:
                    self.logger.debug(
                        "No %s data for %s on %s: %s", prod, site, date_str, exc
                    )
            current += timedelta(days=1)

        for prod in products:
            if prod not in found:
                unavailable.append(prod)

        return {
            "site": site,
            "period": f"{start_date} to {end_date}",
            "available_products": available,
            "unavailable": unavailable,
        }

    # ------------------------------------------------------------------
    # Unified search
    # ------------------------------------------------------------------
    def search_site(self, keyword: str) -> Dict[str, List[Dict[str, Any]]]:
        """Search for a site by keyword across both ARM and CloudNet."""
        keyword = keyword.lower()
        arm_matches = [
            {"code": code, "name": name, "source": "ARM"}
            for code, name in self.arm.COMMON_SITES.items()
            if keyword in code.lower() or keyword in name.lower()
        ]
        cn_matches = [
            {"code": code, "name": name, "source": "CloudNet"}
            for code, name in self.cloudnet.COMMON_SITES.items()
            if keyword in code.lower() or keyword in name.lower()
        ]
        return {"arm": arm_matches, "cloudnet": cn_matches}

    # ------------------------------------------------------------------
    # Pretty-print helpers (used by CLI)
    # ------------------------------------------------------------------
    @staticmethod
    def _col_widths(headers: List[str], rows: List[List[Any]]) -> List[int]:
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))
        return widths

    def print_table(self, headers: List[str], rows: List[List[Any]]) -> None:
        """Print a simple ASCII table to stdout."""
        if not rows:
            print("  (no data)")
            return
        widths = self._col_widths(headers, rows)
        sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
        header_line = "| " + " | ".join(
            h.ljust(w) for h, w in zip(headers, widths)
        ) + " |"
        print(sep)
        print(header_line)
        print(sep)
        for row in rows:
            line = "| " + " | ".join(
                str(cell).ljust(w) for cell, w in zip(row, widths)
            ) + " |"
            print(line)
        print(sep)
