# DealFlow AI Backend

FastAPI backend for AI-powered deal flow management and analysis using RAG (Retrieval-Augmented Generation).

## Features

- **RAG Pipeline**: Document ingestion, vectorization, retrieval, and generation
- **Vector Storage**: Weaviate integration for semantic search
- **LLM Integration**: Google Generative AI (Gemini) for question answering
- **Document Processing**: Support for PDF, TXT, DOCX, and Markdown files
- **RESTful API**: FastAPI-based API with comprehensive endpoints
- **Investor Search**: Specialized endpoints for investor data
- **Trend Analysis**: AI-powered trend analysis capabilities

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config/                 # Configuration files
│   │   ├── settings.py         # Application settings
│   │   └── constants.py        # Application constants
│   ├── services/               # Core services
│   │   ├── translation_service.py
│   │   ├── embedding_service.py
│   │   ├── vector_store_service.py
│   │   ├── llm_service.py
│   │   └── reranker_service.py
│   ├── rag/                    # RAG pipeline components
│   │   ├── document_parser.py
│   │   ├── preprocessor.py
│   │   ├── retriever.py
│   │   └── workflow.py
│   ├── api/                    # API routes and models
│   │   ├── routes/
│   │   │   ├── query.py
│   │   │   ├── investors.py
│   │   │   ├── trends.py
│   │   │   └── ingest.py
│   │   └── models/
│   │       ├── request_models.py
│   │       └── response_models.py
│   └── utils/                  # Utility functions
│       ├── logger.py
│       └── helpers.py
├── data/                       # Data directories
│   ├── raw/                    # Raw documents
│   └── processed/              # Processed documents
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## Setup

### Prerequisites

- Python 3.9+
- Weaviate instance (local or cloud)
- Google API key for Generative AI

### Installation

1. Clone the repository and navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy the example env file
cp .env.example .env  # On Windows: copy .env.example .env
# Edit .env with your API keys
```

5. Configure your `.env` file with:
   - `GOOGLE_API_KEY`: Your Google Generative AI API key
   - `WEAVIATE_URL`: Your Weaviate instance URL
   - `WEAVIATE_API_KEY`: Your Weaviate API key (if required)
   - Other configuration as needed

6. Initialize Weaviate collection (optional, will be created automatically):
```bash
python -c "from app.services.vector_store_service import VectorStoreService; import asyncio; asyncio.run(VectorStoreService().initialize_collection())"
```

## Running the Application

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Production Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the server is running, you can access:
- **Interactive API Docs (Swagger)**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Query
- `POST /api/v1/query` - Query documents using RAG

### Investors
- `POST /api/v1/investors/search` - Search for investors

### Trends
- `POST /api/v1/trends/analyze` - Analyze trends

### Ingest
- `POST /api/v1/ingest` - Ingest a single document
- `POST /api/v1/ingest/batch` - Ingest multiple documents
- `GET /api/v1/ingest/stats` - Get ingestion statistics

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check

## Usage Examples

### Ingest a Document

```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/raw/example.pdf",
    "source": "example_source",
    "chunk": true
  }'
```

### Query Documents

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest investment trends?",
    "top_k": 5
  }'
```

## Configuration

All configuration is managed through environment variables in the `.env` file. See `.env.example` template for all available options.

## Development

### Code Style

This project follows PEP 8 style guidelines. Consider using:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

### Testing

(Add your testing framework and commands here)

## License

(Add your license here)

