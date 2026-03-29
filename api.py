from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import os
import shutil
import uuid

from rag_engine import ask_question, evaluate_uploaded_tender

app = FastAPI(title="AI Tender Evaluation System")

# -----------------------------
# CONFIG
# -----------------------------
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "xlsx", "xls"}


# -----------------------------
# REQUEST MODELS
# -----------------------------
class ChatRequest(BaseModel):
    query: str


# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.get("/")
def home():
    return {
        "status": "running",
        "service": "Tender Evaluation API"
    }


# -----------------------------
# CHAT ENDPOINT
# -----------------------------
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        response = ask_question(request.query)

        return {
            "status": "success",
            "data": response
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# FILE VALIDATION
# -----------------------------
def validate_file(filename: str):
    ext = filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}"
        )


# -----------------------------
# UPLOAD + EVALUATE
# -----------------------------
@app.post("/upload-tender")
async def upload_tender(files: List[UploadFile] = File(...)):

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_DIR, session_id)

    os.makedirs(session_dir, exist_ok=True)

    file_paths = []

    try:
        # -----------------------------
        # SAVE FILES
        # -----------------------------
        for file in files:
            validate_file(file.filename)

            path = os.path.join(session_dir, file.filename)

            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_paths.append(path)

        # -----------------------------
        # RUN EVALUATION
        # -----------------------------
        results = evaluate_uploaded_tender(file_paths)

        return {
            "status": "success",
            "session_id": session_id,
            "files_processed": len(file_paths),
            "data": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # -----------------------------
        # CLEANUP (IMPORTANT)
        # -----------------------------
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)