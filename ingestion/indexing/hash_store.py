import json
import os
import hashlib
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class HashStore:
    def __init__(self, filepath: str = "hash_store.json"):
        self.filepath = filepath
        self.store: Dict[str, str] = {}
        self.seen_urls: set = set()
        self.load()

    def load(self):
        """Loads the hash store from disk."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.store = json.load(f)
                logger.info(f"Loaded HashStore with {len(self.store)} records.")
            except Exception as e:
                logger.error(f"Failed to load HashStore: {e}")
                self.store = {}
        else:
            logger.info("No HashStore found. Starting fresh.")
            self.store = {}

    def save(self):
        """Saves the hash store to disk."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.store, f, indent=2)
            logger.info(f"Saved HashStore to {self.filepath}.")
        except Exception as e:
            logger.error(f"Failed to save HashStore: {e}")

    def generate_hash(self, content: str) -> str:
        """Generates a SHA-256 hash for the given content."""
        if not content:
            return ""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def has_changed(self, url: str, content: str) -> bool:
        """
        Checks if the content for the given URL has changed since last run.
        Also marks the URL as seen in the current run.
        """
        self.seen_urls.add(url)
        
        new_hash = self.generate_hash(content)
        old_hash = self.store.get(url)
        
        if old_hash == new_hash:
            return False
            
        return True

    def update_hash(self, url: str, content: str):
        """Updates the hash for a specific URL."""
        new_hash = self.generate_hash(content)
        self.store[url] = new_hash

    def get_deleted_urls(self) -> List[str]:
        """
        Returns a list of URLs that were in the store but NOT seen during the current run.
        (Only useful if the current run was a FULL crawl).
        """
        all_stored_urls = set(self.store.keys())
        deleted_urls = all_stored_urls - self.seen_urls
        return list(deleted_urls)
        
    def remove_url(self, url: str):
        """Removes a URL from the hash store."""
        if url in self.store:
            del self.store[url]
