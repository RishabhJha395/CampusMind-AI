import os
import yaml
import logging
from typing import Dict, List
from app.models.schemas import UniversityConfig

logger = logging.getLogger(__name__)

class UniversityRegistry:
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            # Point to backend/config/universities
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            self.config_dir = os.path.join(base_dir, "config", "universities")
        else:
            self.config_dir = config_dir
            
        self._universities: Dict[str, UniversityConfig] = {}
        self.load_all()

    def load_all(self) -> None:
        """Loads all YAML configurations from the config directory."""
        if not os.path.exists(self.config_dir):
            logger.warning(f"Config directory {self.config_dir} does not exist.")
            return

        for filename in os.listdir(self.config_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(self.config_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if not data:
                            continue
                        
                        config = UniversityConfig(**data)
                        self._universities[config.university_id] = config
                        logger.info(f"Loaded config for {config.university_name} ({config.university_id})")
                except Exception as e:
                    logger.error(f"Failed to load config {filename}: {e}")
                    raise

    def get_university(self, university_id: str) -> UniversityConfig:
        """Get a specific university config by ID."""
        if university_id not in self._universities:
            raise KeyError(f"University '{university_id}' not found in registry.")
        return self._universities[university_id]

    def get_all(self) -> List[UniversityConfig]:
        """Get all loaded university configs."""
        return list(self._universities.values())

# Global registry instance to be loaded at startup
registry = UniversityRegistry()
