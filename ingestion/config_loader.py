import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            # Default to the root config folder (assuming ingestion is in /ingestion)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_dir = os.path.join(base_dir, "config", "universities")
        else:
            self.config_dir = config_dir

    def load_config(self, university_id: str) -> Dict[str, Any]:
        """Loads a specific YAML configuration by university ID."""
        if not os.path.exists(self.config_dir):
            raise FileNotFoundError(f"Config directory {self.config_dir} does not exist.")

        filepath = os.path.join(self.config_dir, f"{university_id}.yaml")
        if not os.path.exists(filepath):
            filepath = os.path.join(self.config_dir, f"{university_id}.yml")
            
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration for university '{university_id}' not found.")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                logger.info(f"Loaded config for {university_id}")
                return data
        except Exception as e:
            logger.error(f"Failed to load config {university_id}: {e}")
            raise
