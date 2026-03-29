# AI-Based Tender Evaluation System using RAG

An intelligent system for evaluating tender documents against manufacturer specifications using Retrieval-Augmented Generation (RAG) and rule-based compliance checking.

## 🎯 Features

- **Multi-Format Document Processing**: Supports PDF, DOCX, DOC, XLSX, XLS with robust fallback mechanisms
- **RAG Engine**: LLM-powered Q&A with semantic search over indexed documents
- **Structured Data Extraction**: Automatic extraction of technical specifications (voltage, current, features)
- **Intelligent Tender Evaluation**: Rules-based compliance engine with weighted scoring
- **Manufacturer Filtering**: Smart pre-filtering by product type to reduce evaluation candidates
- **REST API**: FastAPI-powered endpoints for chat and tender evaluation
- **Vector Database**: ChromaDB for efficient document retrieval with embeddings
- **Hallucination Prevention**: Strict prompt engineering to ensure factual responses

## 📋 System Requirements

- **Python**: 3.10+
- **Ollama**: Required for local LLM inference ([Download](https://ollama.ai))
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 2GB for embeddings and vector database

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Krishna0625/AI-Based-Tender-Evaluation-System-using-RAG.git
cd AI-Based-Tender-Evaluation-System-using-RAG

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Ollama

Download and install Ollama from [ollama.ai](https://ollama.ai)

Pull the TinyLLaMA model:
```bash
ollama pull tinyllama
ollama serve  # Start Ollama server (keep running in background)
```

### 3. Prepare Manufacturer Documents

Place manufacturer specification documents in the `manufacturer_docs/` folder:
- PDF files (`.pdf`)
- Word documents (`.docx`, `.doc`)
- Excel files (`.xlsx`, `.xls`)

### 4. Index Manufacturer Data

```bash
# Ingest and index manufacturer documents
python run_ingestion.py
```

✅ You'll see success message confirming chunks and records indexed.

### 5. Start the API Server

```bash
python main.py
```

Server runs at: `http://localhost:8000`

## 📖 API Usage

### Health Check
```bash
GET /
```

### Tender Evaluation
```bash
POST /evaluate
Content-Type: multipart/form-data

# Upload one or more tender documents
files: [path/to/tender1.pdf, path/to/tender2.docx]
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "status": "success",
    "evaluations": [
      {
        "tender_item": { ... },
        "best_match": {
          "manufacturer": { ... },
          "evaluation": {
            "score": 85,
            "status": "APPROVED",
            "results": [ ... ]
          }
        },
        "all_matches": [ ... ]
      }
    ]
  }
}
```

### Chat (Q&A over Documents)
```bash
POST /chat
Content-Type: application/json

{
  "query": "What is the voltage specification for battery chargers?"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "answer": "The voltage specification for battery chargers is...",
    "sources": [...]
  }
}
```

## 📁 Project Structure

```
.
├── main.py                      # FastAPI application entry point
├── api.py                       # Additional API endpoints (v2)
├── rag_engine.py               # RAG engine & tender evaluation logic
├── ingestion.py                # Document processing & vector DB
├── Evaluator.py                # Compliance evaluation engine
├── run_ingestion.py            # Batch ingestion script
│
├── requirements.txt            # Production dependencies
├── requirements_test.txt       # Testing dependencies
├── requirements_final.txt      # Final pinned versions
│
├── manufacturer_docs/          # Manufacturer spec documents
├── tender_docs/               # Sample tender documents
├── uploaded_files/            # User-uploaded tender files
├── vectordb/                  # ChromaDB storage
│   ├── manufacturer_db/       # Indexed manufacturer data
│   └── tender_temp/           # Temporary tender indexes
│
└── README.md                  # This file
```

## 🔍 How It Works

### Document Ingestion
1. Load documents in multiple formats
2. Extract structured data (voltage, current, features)
3. Split into 800-character chunks with 100-char overlap
4. Generate embeddings using `sentence-transformers/all-MiniLM-L6-v2`
5. Store in ChromaDB with metadata

### Tender Evaluation
1. Ingest uploaded tender documents
2. Extract specifications from tender
3. **Filter manufacturers** by product type
4. **Evaluate each candidate** against tender requirements:
   - Product type (critical, exact match)
   - Voltage (critical, exact match)
   - Current (critical, >= logic)
   - Features (non-critical, partial scoring)
5. Generate compliance score and final decision:
   - **APPROVED**: ≥80% compliance
   - **CONDITIONAL**: 60-79% compliance
   - **REJECTED**: <60% compliance or critical failures

### RAG Chat
1. User query → Semantic search (k=3 documents)
2. Retrieved context + query → LLM
3. Strict prompt prevents hallucination
4. Response + source metadata

## ⚙️ Configuration

### Model Selection
In `rag_engine.py`, change the LLM model:
```python
LLM_MODEL = "tinyllama"  # Options: tinyllama, llama2, neural-chat, etc.
```

### Embedding Model
In `ingestion.py`:
```python
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
```

### Evaluation Rules
In `Evaluator.py`, adjust weights and thresholds:
```python
rules = {
    "product_type": {"type": "exact", "weight": 20, "critical": True},
    "voltage": {"type": "exact", "weight": 15, "critical": True},
    "current": {"type": "min", "weight": 20, "critical": True},
    "features": {"type": "list", "weight": 10, "critical": False}
}
```

## 🧪 Testing

Run tests with:
```bash
pip install -r requirements_test.txt
pytest  # If test suite is added
```

## 🐛 Troubleshooting

### "Ollama connection refused"
```bash
# Start Ollama server
ollama serve
```

### "No documents retrieved"
- Verify `manufacturer_docs/` has documents
- Run `python run_ingestion.py` again
- Check vectordb folder for new entries

### Memory issues with large PDFs
- Reduce `chunk_size` in `ingestion.py` (e.g., 400 instead of 800)
- Process documents in batches

### Slow responses
- Ollama model might be still loading
- Try lightweight model: `ollama pull neural-chat`
- Run: `LLM_MODEL = "neural-chat"`

## 📊 Performance Optimizations

✅ **Multi-layer document loading fallback** - Prevents single corrupt file from breaking pipeline  
✅ **Efficient text chunking** - 800 chars with overlap balances context & relevance  
✅ **Lightweight embeddings** - Fast inference with good quality  
✅ **Manufacturer pre-filtering** - Reduces evaluation candidates dramatically  
✅ **Early retrieval exit** - Skip LLM if no documents found  
✅ **Structured + Vector dual storage** - Fast filtering + semantic search  
✅ **Streaming file uploads** - No in-memory buffering  

## 🔒 Security Notes

- Store sensitive API keys in `.env` (not in repo)
- Validate file types before processing
- Consider rate limiting for production
- Add authentication for API endpoints

## 📝 Example Workflow

```bash
# 1. Prepare environment
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt

# 2. Start Ollama (in another terminal)
ollama serve

# 3. Ingest manufacturer data
python run_ingestion.py

# 4. Launch API
python main.py

# 5. Upload and evaluate tender
curl -X POST "http://localhost:8000/evaluate" \
  -F "files=@path/to/tender.pdf"

# 6. Ask questions
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the voltage specifications?"}'
```

## 🚀 Future Enhancements

- [ ] Web UI dashboard
- [ ] Batch evaluation with reports
- [ ] Advanced NLP with spaCy for better extraction
- [ ] Support for more document types (PowerPoint, images)
- [ ] Database backend for persistence
- [ ] Role-based access control
- [ ] Audit logging
- [ ] CI/CD pipeline

## 📄 License

MIT License - Feel free to use and modify

## 👤 Author

Krishna Kumawat

## � Contributors

- **Krishna Pavuluri** - Lead Developer & Architecture

## �📧 Support

For issues and questions, please open an issue on [GitHub Issues](https://github.com/Krishna0625/AI-Based-Tender-Evaluation-System-using-RAG/issues)

---

**Built with ❤️ using FastAPI, LangChain, ChromaDB, and Ollama**
