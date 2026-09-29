# Donna — AI Contract Analysis API

Donna is a REST API that reads legal contracts and turns them into structured, easy-to-understand analysis. Upload a PDF or TXT contract, and Donna uses Google's Gemini models to produce a plain-language summary, the key clauses, risk flags with recommendations, and an overall risk rating, all validated with Pydantic and stored in MongoDB.

The analysis prompt is tuned for **Indian contract law**.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-009688) ![MongoDB](https://img.shields.io/badge/MongoDB-47A248) ![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

---

## Features

- **Upload contracts** as PDF or TXT (max 10 MB) with automatic text extraction
- **AI-powered analysis** via the Gemini API, returning:
  - a short summary and contract type (NDA, service agreement, etc.)
  - key clauses with a plain-English explanation and a standard / non-standard flag
  - risk flags rated `low`, `medium`, `high` or `critical`, each with a recommendation and clause reference
  - an overall risk level and a list of recommendations
- **Strict schema validation** with Pydantic so responses are consistent
- **Persistent storage** of contracts and analyses in MongoDB, with indexes for fast lookup
- **Multiple analyses per contract**, retrievable by analysis ID or contract ID
- **Interactive API docs** from FastAPI at `/docs`

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI, Uvicorn |
| AI | Google Gemini (`google-genai`) |
| Validation | Pydantic |
| Database | MongoDB (PyMongo) |
| Document parsing | PyPDF2 |
| Infrastructure | Docker Compose (MongoDB) |

## Project Structure

```
Donna/
├── docker-compose.yml        # MongoDB container
├── requirements.txt
└── app/
    ├── main.py               # FastAPI app, startup hook, root endpoint
    ├── config.py             # Env vars and upload limits
    ├── database.py           # MongoDB client, collections, indexes
    ├── models.py             # Pydantic models (Contact, AnalysisResult, RiskFlag, ...)
    ├── routes/
    │   ├── contracts.py      # Upload / list / fetch contracts
    │   └── analysis.py       # Run and fetch analyses
    ├── service/
    │   ├── document_parser.py  # PDF and TXT text extraction
    │   ├── gemini_analyse.py   # Gemini call + response parsing
    │   └── prompt.py           # Prompt templates
    └── uploads/              # Uploaded files (created at runtime)
```

## How It Works

```
Upload PDF/TXT ──► Validate type & size ──► Extract text ──► Store in MongoDB
                                                                   │
        Structured JSON  ◄── Pydantic validation ◄── Gemini ◄── POST /analysis/analyse/{id}
                │
                └──► Saved to MongoDB and returned to the client
```

1. `POST /contracts/upload` validates the file, saves it, extracts its text and stores the contract.
2. `POST /analysis/analyse/{contract_id}` sends the contract text (first 15,000 characters) to Gemini with a structured prompt.
3. The JSON response is parsed into `ClauseAnalysis` and `RiskFlag` models, wrapped in an `AnalysisResult`, saved, and returned.

## Getting Started

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- A [Gemini API key](https://aistudio.google.com/apikey)

### 1. Clone and install

```bash
git clone <your-repo-url>
cd Donna

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
pip install google-genai        # used by the analysis service
```

### 2. Start MongoDB

```bash
docker compose up -d
```

This starts MongoDB on port `27017` with the credentials defined in `docker-compose.yml`. Change the default password before using this anywhere beyond local development.

### 3. Configure environment variables

Create `app/.env`:

```env
MONGODB_URI=mongodb://root:mypassword@localhost:27017
GEMINI_API_KEY=your_gemini_api_key_here
```

> ⚠️ Never commit `.env` to version control. Add it to `.gitignore`.

### 4. Run the API

The app uses top-level imports, so run it from inside the `app/` directory:

```bash
cd app
uvicorn main:app --reload
```

The API is now available at `http://localhost:8000`, and the interactive docs at `http://localhost:8000/docs`.

## API Reference

### Contracts

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/contracts/upload` | Upload a PDF or TXT contract (multipart form, field `file`) |
| `GET` | `/contracts/` | List all contracts (without full text) |
| `GET` | `/contracts/{contract_id}` | Get a single contract, including extracted text |

### Analysis

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analysis/analyse/{contract_id}` | Analyze a contract with Gemini |
| `GET` | `/analysis/` | List all analyses |
| `GET` | `/analysis/{analysis_id}` | Get a specific analysis |
| `GET` | `/analysis/contract/{contract_id}` | Get all analyses for a contract |

### Example usage

**Upload a contract**

```bash
curl -X POST http://localhost:8000/contracts/upload \
  -F "file=@nda.pdf"
```

```json
{
  "message": "File uploaded and processed successfully",
  "contract": {
    "id": "665f1c...",
    "original_name": "nda.pdf",
    "page_count": 4,
    "word_count": 1820,
    "status": "uploaded"
  },
  "id": "665f1c..."
}
```

**Analyze it**

```bash
curl -X POST http://localhost:8000/analysis/analyse/665f1c...
```

```json
{
  "message": "Contract analyzed successfully",
  "analysis": {
    "contract_id": "665f1c...",
    "summary": "A mutual NDA between two Indian companies...",
    "contract_type": "Non-Disclosure Agreement",
    "key_clauses": [
      {
        "clause_title": "Confidentiality Period",
        "clause_text": "...",
        "explanation": "How long the information must be kept secret.",
        "is_standard": true
      }
    ],
    "risk_flags": [
      {
        "risk_title": "One-sided termination",
        "description": "...",
        "risk_level": "medium",
        "recommendation": "Negotiate mutual termination rights.",
        "clause_reference": "Clause 8"
      }
    ],
    "overall_risk_level": "medium",
    "recommendations": ["..."]
  },
  "id": "665f2a..."
}
```

## Configuration

Defaults live in `app/config.py`:

| Setting | Default | Description |
|---|---|---|
| `ALLOWED_EXTENSIONS` | `.pdf`, `.txt` | Accepted upload types |
| `MAX_FILE_SIZE_MB` | `10` | Maximum upload size |
| `UPLOAD_DIR` | `uploads` | Where uploaded files are saved |
| `MONGODB_URI` | from `.env` | MongoDB connection string |
| `GEMINI_API_KEY` | from `.env` | Gemini API key |

## Known Limitations and Roadmap

- Only the first 15,000 characters of a contract are analyzed; long documents should be chunked
- Scanned or image-only PDFs are not supported (no OCR yet)
- Add validation for malformed contract IDs (currently an invalid ID raises a server error instead of a 400)
- Add authentication and per-user contract storage
- Containerize the API service itself alongside MongoDB
- Add tests and CI

## Disclaimer

Donna provides automated analysis for informational purposes only. It is not legal advice and does not replace review by a qualified lawyer.
