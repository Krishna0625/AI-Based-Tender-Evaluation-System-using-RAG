import os
from ingestion import ingest_documents

DIR = "manufacturer_docs"

files = [os.path.join(DIR, f) for f in os.listdir(DIR)]

print("🔒 Ingesting Manufacturer Docs...")

ingest_documents(
    file_paths=files,
    persist_directory="vectordb/manufacturer_db",
    doc_type="manufacturer"
)

print("✅ Done!")