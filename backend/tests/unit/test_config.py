import os
import tempfile
import yaml
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.models.schemas import UniversityConfig
from app.config.universities.registry import UniversityRegistry
from app.main import app

# Sample valid config for testing
VALID_CONFIG = {
    "university_id": "test_uni",
    "university_name": "Test University",
    "short_name": "TU",
    "website_url": "https://test.edu",
    "crawler": {
        "start_urls": ["https://test.edu"],
        "allowed_domains": ["test.edu"],
    },
    "pdf": {
        "auto_discover": True
    },
    "vector_store": {
        "collection_name": "test_vectors"
    },
    "branding": {
        "primary_color": "#000000",
        "secondary_color": "#ffffff",
        "logo_url": "/logo.png",
        "welcome_message": "Welcome"
    },
    "connectors": [
        {"type": "website"}
    ],
    "metadata": {
        "categories": ["general"]
    }
}

def test_registry_loads_valid_yaml():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a valid yaml file
        file_path = os.path.join(tmpdir, "test.yaml")
        with open(file_path, "w") as f:
            yaml.dump(VALID_CONFIG, f)
            
        registry = UniversityRegistry(config_dir=tmpdir)
        
        assert len(registry.get_all()) == 1
        uni = registry.get_university("test_uni")
        assert uni.university_name == "Test University"
        assert uni.crawler.start_urls == ["https://test.edu"]

def test_registry_invalid_yaml_raises_validation_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an invalid yaml file (missing required fields)
        invalid_config = {"university_id": "bad"}
        file_path = os.path.join(tmpdir, "invalid.yaml")
        with open(file_path, "w") as f:
            yaml.dump(invalid_config, f)
            
        with pytest.raises(ValidationError):
            UniversityRegistry(config_dir=tmpdir)

def test_api_returns_universities(monkeypatch):
    # Mock the global registry's get_all method
    from app.config.universities.registry import registry
    
    mock_uni = UniversityConfig(**VALID_CONFIG)
    monkeypatch.setattr(registry, "get_all", lambda: [mock_uni])
    
    client = TestClient(app)
    response = client.get("/api/v1/universities")
    
    assert response.status_code == 200
    data = response.json()
    assert "universities" in data
    assert len(data["universities"]) == 1
    assert data["universities"][0]["university_id"] == "test_uni"
    assert data["universities"][0]["university_name"] == "Test University"
