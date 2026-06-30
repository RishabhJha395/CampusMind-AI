from typing import List, Optional, Dict
from pydantic import BaseModel, Field, HttpUrl

class CrawlerConfig(BaseModel):
    start_urls: List[str]
    allowed_domains: List[str]
    max_depth: int = 5
    max_pages: int = 2000
    respect_robots_txt: bool = True
    crawl_delay_seconds: float = 1.0
    ignore_patterns: List[str] = Field(default_factory=list)

class PdfConfig(BaseModel):
    auto_discover: bool = True
    max_file_size_mb: int = 50
    ocr_languages: List[str] = Field(default_factory=lambda: ["eng"])

class VectorStoreConfig(BaseModel):
    collection_name: str
    vector_size: int = 384
    distance_metric: str = "Cosine"

class BrandingConfig(BaseModel):
    primary_color: str
    secondary_color: str
    logo_url: str
    welcome_message: str
    theme: str = "blue"

class ConnectorConfig(BaseModel):
    type: str
    enabled: bool = True

class MetadataConfig(BaseModel):
    categories: List[str] = Field(default_factory=list)
    supported_languages: List[str] = Field(default_factory=list)

class UniversityConfig(BaseModel):
    university_id: str
    university_name: str
    short_name: str
    website_url: str
    crawler: CrawlerConfig
    pdf: PdfConfig
    vector_store: VectorStoreConfig
    branding: BrandingConfig
    connectors: List[ConnectorConfig]
    metadata: MetadataConfig

class UniversityListResponse(BaseModel):
    universities: List[dict]
