import json
import os
import shutil

from ingestion import ingest_documents
from Evaluator import evaluate_tender

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM


# -----------------------------
# EMBEDDINGS
# -----------------------------
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# -----------------------------
# LLM MODEL
# -----------------------------
LLM_MODEL = "tinyllama"


# -----------------------------
# CHAT (IMPROVED RAG)
# -----------------------------
def ask_question(query, model_name=LLM_MODEL):

    vectordb = Chroma(
        persist_directory="vectordb/manufacturer_db",
        embedding_function=embeddings
    )

    # 🔍 Force retrieval check
    docs = vectordb.similarity_search(query, k=3)
    
    print("Retrieved docs:", docs)  # DEBUG
    
    # Early exit if no documents found
    if not docs:
        print("[WARNING] No documents retrieved!")
        return {"answer": "Not available", "sources": []}

    # Build proper context
    context = "\n\n".join([doc.page_content for doc in docs])

    llm = OllamaLLM(model=model_name)

    # Strong prompt (fix hallucination)
    prompt = f"""You are a strict assistant.

RULES:
- Answer ONLY from the given context
- If answer not found, say "Not available"
- Do NOT guess

Context:
{context}

Question:
{query}

Answer:
"""

    response = llm.invoke(prompt)

    return {
        "answer": response,
        "sources": [d.metadata for d in docs]
    }


# -----------------------------
# FILTER MANUFACTURERS (NEW)
# -----------------------------
def filter_manufacturers(tender, manufacturer_data):

    filtered = []

    t_type = tender.get("product_type", "").lower()

    for m in manufacturer_data:
        if m.get("product_type", "").lower() == t_type:
            filtered.append(m)

    return filtered if filtered else manufacturer_data  # fallback


# -----------------------------
# LOAD STRUCTURED DATA
# -----------------------------
def load_json(path):
    with open(path) as f:
        return json.load(f)


# -----------------------------
# DYNAMIC TENDER EVALUATION (UPGRADED)
# -----------------------------
def evaluate_uploaded_tender(file_paths):

    temp_db = "vectordb/tender_temp"

    # Clean old temp DB
    if os.path.exists(temp_db):
        shutil.rmtree(temp_db)

    # Ingest tender
    ingest_documents(
        file_paths=file_paths,
        persist_directory=temp_db,
        doc_type="tender"
    )

    # Load structured data
    tender_data = load_json(f"{temp_db}/tender_structured.json")
    manufacturer_data = load_json("vectordb/manufacturer_db/manufacturer_structured.json")

    final_results = []

    # -----------------------------
    # PROCESS EACH TENDER ITEM
    # -----------------------------
    for t in tender_data:

        # 🔥 Step 1: Filter manufacturers
        candidates = filter_manufacturers(t, manufacturer_data)

        best_result = None
        best_score = -1

        all_results = []

        # 🔥 Step 2: Evaluate each candidate
        for m in candidates:
            result = evaluate_tender(t, m)

            all_results.append({
                "manufacturer": m,
                "evaluation": result
            })

            if result["score"] > best_score:
                best_score = result["score"]
                best_result = {
                    "manufacturer": m,
                    "evaluation": result
                }

        # 🔥 Step 3: Final decision
        final_results.append({
            "tender_item": t,
            "best_match": best_result,
            "all_matches": all_results
        })

    return {
        "status": "success",
        "evaluations": final_results
    }