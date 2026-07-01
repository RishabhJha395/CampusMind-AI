import argparse
import asyncio
import logging
import os
from ingestion.config_loader import ConfigLoader
from ingestion.connectors.web_crawler import WebCrawler
from ingestion.chunking.text_chunker import TextChunker
from ingestion.indexing.hash_store import HashStore
from app.services.embedding.local_embedder import LocalEmbedder
from app.services.vector_store.qdrant_store import QdrantStore
from qdrant_client.http import models

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_pipeline(university_id: str, tier: str):
    logger.info(f"Starting ingestion pipeline for {university_id} (Tier: {tier})")
    
    # 1. Load config
    loader = ConfigLoader()
    try:
        config = loader.load_config(university_id)
        uni_name = config.get("university_name", university_id)
    except FileNotFoundError as e:
        logger.error(str(e))
        return
        
    # Get crawler settings
    crawler_config = config.get("crawler", {})
    start_urls = crawler_config.get("start_urls", [])
    max_depth = crawler_config.get("max_depth", 2)
    max_pages = crawler_config.get("max_pages", 2000)
    
    if tier == "fast":
        logger.info("Fast tier active. Overriding start_urls and max_depth.")
        max_depth = 1
        max_pages = 50
        # Focus on notice boards and updates
        start_urls = ["https://dtu.ac.in/Web/notice/", "https://dtu.ac.in/"]

    if not start_urls:
        logger.error("No start URLs found in configuration.")
        return

    # 2. Initialize components
    crawler = WebCrawler(
        university_id=university_id,
        start_urls=start_urls,
        max_depth=max_depth,
        max_pages=max_pages
    )
    
    chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
    
    embedder = LocalEmbedder(
        model_name=os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    )
    
    vector_store = QdrantStore(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY", None)
    )
    
    hash_store = HashStore("hash_store.json")
    
    collection_name = config.get("vector_store", {}).get("collection_name", f"{university_id}_vectors")
    vector_size = config.get("vector_store", {}).get("vector_size", 384)
    distance_metric = config.get("vector_store", {}).get("distance_metric", "Cosine")
    
    vector_store.create_collection(collection_name, vector_size, distance_metric)
    
    docs_processed = 0
    chunks_processed = 0
    skipped_docs = 0
    
    # Helper to process and upload a document incrementally
    async def process_document(document):
        nonlocal docs_processed, chunks_processed, skipped_docs
        
        url = document.metadata.source_url
        content = document.content
        
        # 3. Check HashStore for changes
        if not hash_store.has_changed(url, content):
            skipped_docs += 1
            logger.debug(f"Skipped unchanged document: {url}")
            return
            
        logger.info(f"Changes detected for {url}. Processing...")
        
        chunks = chunker.chunk_document(document)
        if not chunks:
            return
            
        # 4. Delete old vectors for this URL if they exist
        try:
            vector_store.client.delete(
                collection_name=collection_name,
                points_selector=models.Filter(
                    must=[models.FieldCondition(key="source_url", match=models.MatchValue(value=url))]
                )
            )
        except Exception as e:
            logger.warning(f"Could not delete old vectors for {url}: {e}")
            
        # 5. Embed and Insert new vectors
        texts_to_embed = [chunk.content for chunk in chunks]
        metadatas = [chunk.metadata.model_dump() for chunk in chunks]
        
        vectors = embedder.embed_texts(texts_to_embed)
        
        points = []
        for i, chunk in enumerate(chunks):
            payload = metadatas[i]
            payload["content"] = chunk.content
            
            points.append({
                "id": chunk.id,
                "vector": vectors[i],
                "payload": payload
            })
            
        vector_store.upsert(collection_name, points)
        
        # 6. Update HashStore
        hash_store.update_hash(url, content)
        
        docs_processed += 1
        chunks_processed += len(chunks)
        
        # 6.5 Periodic Save
        if docs_processed % 50 == 0:
            logger.info(f"Checkpoint: Saving HashStore at {docs_processed} documents...")
            hash_store.save()

    # Crawl Web Pages
    async for document in crawler.extract():
        await process_document(document)
        
    # Process Discovered PDFs
    pdf_urls = list(crawler.discovered_pdfs)
    if pdf_urls:
        def sort_key(url):
            u = url.lower()
            if "2026" in u: return 0
            if "2025" in u: return 1
            if "ordinance" in u or "rule" in u or "schedule" in u or "policy" in u: return 2
            return 3
            
        pdf_urls.sort(key=sort_key)
        pdf_urls = pdf_urls[:1500]
        
        from ingestion.connectors.pdf_connector import PDFConnector
        logger.info(f"Processing {len(pdf_urls)} high-priority PDFs...")
        
        pdf_connector = PDFConnector(
            university_id=university_id,
            pdf_urls=pdf_urls,
            ocr_languages=["eng"]
        )
        
        async for document in pdf_connector.extract():
            await process_document(document)
            
    # 7. Handle Deletions (only on full tier)
    if tier == "full":
        deleted_urls = hash_store.get_deleted_urls()
        logger.info(f"Full tier run complete. Found {len(deleted_urls)} deleted/orphaned URLs.")
        for url in deleted_urls:
            try:
                vector_store.client.delete(
                    collection_name=collection_name,
                    points_selector=models.Filter(
                        must=[models.FieldCondition(key="source_url", match=models.MatchValue(value=url))]
                    )
                )
                hash_store.remove_url(url)
                logger.info(f"Deleted vectors for orphaned URL: {url}")
            except Exception as e:
                logger.error(f"Failed to delete orphaned URL {url}: {e}")
                
    # 8. Save HashStore state
    hash_store.save()
            
    logger.info(f"Ingestion completed. Processed: {docs_processed}, Skipped: {skipped_docs}, New Chunks: {chunks_processed}.")

def main():
    parser = argparse.ArgumentParser(description="CampusMind AI Ingestion Pipeline")
    parser.add_argument("--university", type=str, required=True, help="ID of the university to ingest (e.g., dtu)")
    parser.add_argument("--tier", type=str, choices=["fast", "full"], default="full", help="Crawl tier (fast=notices only, full=everything)")
    args = parser.parse_args()
    
    asyncio.run(run_pipeline(args.university, args.tier))

if __name__ == "__main__":
    main()
