"""Configuration management for ARM and CloudNet data fetchers."""

import os
import yaml
from typing import Optional, Dict, Any
from pathlib import Path


class Config:
    """Configuration manager supporting YAML and environment variables."""

    DEFAULT_CONFIG = {
        "arm": {
            "base_url": "https://adc.arm.gov/armlive/data/query",
            "token": None,
            "output_dir": "./data/arm",
            "timeout": 300,
            "retry_times": 3,
        },
        "cloudnet": {
            "base_url": "https://cloudnet.fmi.fi/api",
            "output_dir": "./data/cloudnet",
            "timeout": 300,
            "retry_times": 3,
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        self._config = self._load_config(config_path)

    def _load_config(self, path: Optional[str]) -> Dict[str, Any]:
        config = self.DEFAULT_CONFIG.copy()
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            self._deep_update(config, user_config)
        self._apply_env_overrides(config)
        return config

    def _deep_update(self, base: Dict, update: Dict) -> None:
        for key, value in update.items():
            if isinstance(value, dict) and key in base:
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        if os.getenv("ARM_TOKEN"):
            config["arm"]["token"] = os.getenv("ARM_TOKEN")
        if os.getenv("ARM_OUTPUT_DIR"):
            config["arm"]["output_dir"] = os.getenv("ARM_OUTPUT_DIR")
        if os.getenv("CLOUDNET_OUTPUT_DIR"):
            config["cloudnet"]["output_dir"] = os.getenv("CLOUDNET_OUTPUT_DIR")

    def get(self, section: str, key: Optional[str] = None) -> Any:
        if key is None:
            return self._config.get(section, {})
        return self._config.get(section, {}).get(key)

    def ensure_directories(self) -> None:
        Path(self.get("arm", "output_dir")).mkdir(parents=True, exist_ok=True)
        Path(self.get("cloudnet", "output_dir")).mkdir(parents=True, exist_ok=True)
