import os

folders = [
    "backend/app/config/universities",
    "backend/app/api/v1",
    "backend/app/core",
    "backend/app/models",
    "backend/app/services/llm",
    "backend/app/services/retrieval",
    "backend/app/services/embedding",
    "backend/app/services/vector_store",
    "backend/app/utils",
    "backend/tests/unit",
    "backend/tests/integration",
    "ingestion/crawlers",
    "ingestion/processors",
    "ingestion/chunking",
    "ingestion/embedding",
    "ingestion/indexing",
    "ingestion/pipeline",
    "ingestion/config",
    "config/universities",
    ".github/workflows"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    init_path = os.path.join(folder, "__init__.py")
    if "backend/app" in folder or "ingestion" in folder:
        open(init_path, 'w').close()

open("backend/app/__init__.py", "w").close()
open("backend/tests/__init__.py", "w").close()
open("ingestion/__init__.py", "w").close()

print("Directories created successfully!")
