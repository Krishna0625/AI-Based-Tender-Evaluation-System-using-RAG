import os
import json
import re
import pandas as pd
from typing import List, Dict

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredFileLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# -------------------------------
# EMBEDDING MODEL
# -------------------------------
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# -------------------------------
# LOAD DOCUMENTS (ROBUST MULTI-LAYER FALLBACK)
# -------------------------------
def load_document(file_path: str) -> List[Document]:
    """
    Load documents with multi-layer fallback system:
    1. Try native loader (PyPDF, Docx2txt, etc.)
    2. Try UnstructuredFileLoader (universal)
    3. Return empty list if completely fails
    """
    try:
        # 1️⃣ PDF FILES
        if file_path.endswith(".pdf"):
            try:
                return PyPDFLoader(file_path).load()
            except Exception as pdf_err:
                print(f"⚠️ PyPDF failed, using fallback for {file_path}")
                print(f"   Error: {pdf_err}")
                try:
                    return UnstructuredFileLoader(file_path).load()
                except Exception as fallback_err:
                    print(f"❌ Both PDF loaders failed for {file_path}")
                    print(f"   Error: {fallback_err}")
                    return []

        # 2️⃣ DOCX FILES
        elif file_path.endswith(".docx"):
            try:
                return Docx2txtLoader(file_path).load()
            except Exception as docx_err:
                print(f"⚠️ Docx2txt failed, fallback to unstructured: {file_path}")
                print(f"   Error: {docx_err}")
                try:
                    return UnstructuredFileLoader(file_path).load()
                except Exception as fallback_err:
                    print(f"❌ Both DOCX loaders failed for {file_path}")
                    print(f"   Error: {fallback_err}")
                    return []

        # 3️⃣ OLD DOC FILES
        elif file_path.endswith(".doc"):
            print(f"⚠️ Handling legacy .doc file using unstructured: {file_path}")
            try:
                return UnstructuredFileLoader(file_path).load()
            except Exception as doc_err:
                print(f"❌ Doc loader failed for {file_path}")
                print(f"   Error: {doc_err}")
                return []

        # 4️⃣ EXCEL FILES
        elif file_path.endswith((".xlsx", ".xls")):
            try:
                return UnstructuredExcelLoader(file_path).load()
            except Exception as excel_err:
                print(f"⚠️ Excel loader failed, fallback: {file_path}")
                print(f"   Error: {excel_err}")
                try:
                    return UnstructuredFileLoader(file_path).load()
                except Exception as fallback_err:
                    print(f"❌ Both Excel loaders failed for {file_path}")
                    print(f"   Error: {fallback_err}")
                    return []

        # 5️⃣ ANY OTHER FILE TYPE
        else:
            print(f"⚠️ Unknown type, using universal loader: {file_path}")
            try:
                return UnstructuredFileLoader(file_path).load()
            except Exception as universal_err:
                print(f"❌ Universal loader failed for {file_path}")
                print(f"   Error: {universal_err}")
                return []

    except Exception as e:
        print(f"❌ CRITICAL: Unexpected error loading {file_path}")
        print(f"   Error: {e}")
        return []


# -------------------------------
# NORMALIZATION HELPERS
# -------------------------------
def normalize_voltage(value: str):
    if not value:
        return None

    value = value.replace(" ", "").upper()

    if "KV" in value:
        num = float(re.findall(r"\d+\.?\d*", value)[0])
        return int(num * 1000)

    elif "V" in value:
        return int(re.findall(r"\d+", value)[0])

    return None


def normalize_current(value: str):
    if not value:
        return None

    value = value.replace(" ", "").upper()
    return int(re.findall(r"\d+", value)[0])


# -------------------------------
# EXTRACTION (IMPROVED)
# -------------------------------
def extract_voltage(text: str):
    matches = re.findall(r"\b\d{2,4}\s?(?:V|kV)\b", text, re.IGNORECASE)
    return matches


def extract_current(text: str):
    matches = re.findall(r"\b\d{1,4}\s?A\b", text, re.IGNORECASE)
    return matches


def extract_product_type(text: str):
    text = text.lower()

    if "battery" in text:
        return "battery"
    elif "charger" in text:
        return "charger"
    elif "motor" in text:
        return "motor"

    return "unknown"


def extract_features(text: str):
    keywords = [
        "fast charging",
        "overload protection",
        "auto cut",
        "thermal protection",
        "redundancy",
        "dual charger"
    ]

    return [k for k in keywords if k in text.lower()]


# -------------------------------
# STRUCTURED EXTRACTION
# -------------------------------
def extract_structured_data(text: str, source: str, page: int) -> Dict:
    voltages = extract_voltage(text)
    currents = extract_current(text)

    return {
        "product_type": extract_product_type(text),
        "parameters": {
            "voltage": [
                {
                    "raw": v,
                    "normalized": normalize_voltage(v)
                } for v in voltages
            ],
            "current": [
                {
                    "raw": c,
                    "normalized": normalize_current(c)
                } for c in currents
            ]
        },
        "features": extract_features(text),
        "source": {
            "file": source,
            "page": page,
            "snippet": text[:200]  # first 200 chars
        }
    }


# -------------------------------
# INGEST DOCUMENTS
# -------------------------------
def ingest_documents(file_paths: List[str], persist_directory: str, doc_type="manufacturer"):

    os.makedirs(persist_directory, exist_ok=True)

    documents = []
    structured_data = []

    for file_path in file_paths:
        docs = load_document(file_path)

        for i, doc in enumerate(docs):
            doc.metadata["doc_type"] = doc_type
            doc.metadata["source"] = file_path
            doc.metadata["page"] = i + 1

            documents.append(doc)

            structured_data.append(
                extract_structured_data(
                    doc.page_content,
                    file_path,
                    i + 1
                )
            )

    # -------------------------------
    # SAVE STRUCTURED JSON
    # -------------------------------
    structured_path = os.path.join(
        persist_directory,
        f"{doc_type}_structured.json"
    )

    with open(structured_path, "w") as f:
        json.dump(structured_data, f, indent=2)

    # -------------------------------
    # CHUNKING
    # -------------------------------
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(documents)

    # -------------------------------
    # ADD METADATA TO CHUNKS
    # -------------------------------
    for chunk in chunks:
        chunk.metadata.update({
            "doc_type": doc_type
        })

    # -------------------------------
    # VECTOR DB (SAFE APPEND)
    # -------------------------------
    vectordb = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )

    vectordb.add_documents(chunks)

    return {
        "status": "success",
        "chunks": len(chunks),
        "records": len(structured_data),
        "structured_file": structured_path
    }