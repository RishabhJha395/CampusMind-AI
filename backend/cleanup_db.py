import os
import re
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchText, MatchAny

def clean_old_vectors():
    db_path = os.path.join(os.path.dirname(__file__), "..", "qdrant_data")
    print(f"Connecting to Qdrant at {db_path}...")
    client = QdrantClient(path=db_path)
    
    collection_name = "dtu_vectors"
    
    # Check if collection exists
    try:
        info = client.get_collection(collection_name)
        print(f"Initial points count: {info.points_count}")
    except Exception as e:
        print(f"Collection not found: {e}")
        return

    # Delete points where source_url contains old years
    years_to_remove = ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
    
    deleted_count = 0
    
    # Qdrant local mode doesn't perfectly support MatchAny on substring, so we'll scroll and delete
    offset = None
    batch_size = 1000
    points_to_delete = []
    
    print("Scanning for old documents...")
    while True:
        records, next_page = client.scroll(
            collection_name=collection_name,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
        
        for record in records:
            url = record.payload.get("source_url", "").lower()
            title = record.payload.get("document_title", "").lower()
            
            # Check if URL or Title contains an old year
            has_old_year = False
            for year in years_to_remove:
                if year in url:
                    has_old_year = True
                    break
                    
            if has_old_year:
                points_to_delete.append(record.id)
                
        if next_page is None:
            break
        offset = next_page
        print(f"Scanned... Found {len(points_to_delete)} to delete so far")
        
    if points_to_delete:
        print(f"Deleting {len(points_to_delete)} old vectors...")
        # Delete in batches to avoid overwhelming local sqlite
        batch_del = 1000
        for i in range(0, len(points_to_delete), batch_del):
            client.delete(
                collection_name=collection_name,
                points_selector=points_to_delete[i:i+batch_del]
            )
        print("Deletion complete.")
    else:
        print("No old vectors found.")
        
    info = client.get_collection(collection_name)
    print(f"Final points count: {info.points_count}")

if __name__ == "__main__":
    clean_old_vectors()
