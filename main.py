from fastapi import FastAPI, UploadFile, File
from typing import List
import shutil
import os

from rag_engine import ask_question, evaluate_uploaded_tender

app = FastAPI(title="AI Tender Evaluation System")


# -------------------------------
# SAFETY CHECK: Manufacturer Data
# -------------------------------
def check_manufacturer_data():
    """Verify that manufacturer data has been indexed."""
    path = "vectordb/manufacturer_db/manufacturer_structured.json"
    if not os.path.exists(path):
        raise Exception(
            "❌ Manufacturer data not found. "
            "Please run 'python run_ingestion.py' first to index documents."
        )


# -------------------------------
# 1. Health Check
# -------------------------------
@app.get("/")
def home():
    return {"message": "🚀 AI Tender Evaluation API Running"}


# -------------------------------
# 2. Chat Endpoint
# -------------------------------
@app.post("/chat")
def chat(query: str):
    try:
        response = ask_question(query)
        return {
            "status": "success",
            "answer": response["answer"]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# -------------------------------
# 3. File Upload + Evaluation
# -------------------------------
UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.post("/evaluate")
def evaluate(files: List[UploadFile] = File(...)):
    file_paths = []

    try:
        # Check if manufacturer data is ready
        check_manufacturer_data()
        
        # Save uploaded files
        for file in files:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_paths.append(file_path)

        # Run evaluation
        result = evaluate_uploaded_tender(file_paths)

        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }