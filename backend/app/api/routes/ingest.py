"""
Document Ingestion API Routes with file upload support
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
import logging
import json
from io import BytesIO
import pandas as pd

from app.services.vector_store_service import vector_store_service
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {'.pdf', '.csv', '.json', '.xlsx', '.jsonl'}
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


class IngestionResponse(BaseModel):
    """Response for ingestion operations"""
    success: bool = Field(..., description="Whether ingestion was successful")
    documents_added: int = Field(default=0, description="Number of documents added")
    message: str = Field(..., description="Status message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class IngestionStats(BaseModel):
    """Ingestion statistics"""
    total_documents: int = Field(..., description="Total documents ingested")
    total_size_mb: float = Field(..., description="Total data ingested in MB")
    collections: Dict[str, int] = Field(..., description="Documents per collection")


class URLIngestRequest(BaseModel):
    """URL ingestion request"""
    url: str = Field(..., min_length=10, max_length=2000, description="URL to ingest")
    collection: Optional[str] = Field(None, description="Target collection")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


def validate_file_size(file_size: int) -> None:
    """Validate file size"""
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File exceeds maximum size of {MAX_FILE_SIZE / (1024*1024):.1f} MB")


def validate_file_extension(filename: str) -> str:
    """Validate and return file extension"""
    ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    return ext


async def parse_pdf(content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse PDF and extract text"""
    documents = []
    try:
        try:
            import PyPDF2
        except ImportError:
            logger.warning("PyPDF2 not installed, skipping PDF parsing")
            raise ValueError("PDF parsing not available")
        
        pdf_file = BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        full_text = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            except Exception as e:
                logger.warning(f"Error extracting page {page_num}: {e}")
                continue
        
        if not full_text.strip():
            raise ValueError("No text extracted from PDF")
        
        # Chunk text with overlap
        chunks = chunk_text(full_text, CHUNK_SIZE, CHUNK_OVERLAP)
        
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                documents.append({
                    "content": chunk,
                    "properties": {
                        "chunk_id": i,
                        "total_chunks": len(chunks),
                        "source_file": filename,
                        "document_type": "pdf"
                    }
                })
        
        logger.info(f"Extracted {len(documents)} chunks from PDF")
        return documents
        
    except Exception as e:
        logger.error(f"PDF parsing error: {e}")
        raise ValueError(f"Failed to parse PDF: {str(e)}")


async def parse_csv(content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse CSV file"""
    documents = []
    try:
        df = pd.read_csv(BytesIO(content))
        
        if df.empty:
            raise ValueError("CSV file is empty")
        
        for idx, row in df.iterrows():
            doc = row.to_dict()
            
            # Create content field for embedding
            content_parts = []
            for key, value in doc.items():
                if pd.notna(value):
                    content_parts.append(f"{key}: {value}")
            
            doc['content'] = " | ".join(content_parts)
            doc['properties'] = {
                "row_index": idx,
                "total_rows": len(df),
                "source_file": filename,
                "document_type": "csv"
            }
            
            documents.append(doc)
        
        logger.info(f"Parsed {len(documents)} rows from CSV")
        return documents
        
    except Exception as e:
        logger.error(f"CSV parsing error: {e}")
        raise ValueError(f"Failed to parse CSV: {str(e)}")


async def parse_json(content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse JSON file"""
    documents = []
    try:
        # Try parsing as JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as je:
            raise ValueError(f"Invalid JSON format: {str(je)}")
        
        if isinstance(data, list):
            if not data:
                raise ValueError("JSON array is empty")
            documents = data
        elif isinstance(data, dict):
            documents = [data]
        else:
            raise ValueError("JSON must be an array or object")
        
        # Add document type metadata
        for doc in documents:
            if isinstance(doc, dict):
                if 'properties' not in doc:
                    doc['properties'] = {}
                doc['properties']['source_file'] = filename
                doc['properties']['document_type'] = 'json'
                
                if 'content' not in doc:
                    content_parts = []
                    for key, value in doc.items():
                        if key != 'properties' and value:
                            content_parts.append(f"{key}: {value}")
                    doc['content'] = " | ".join(content_parts)
        
        logger.info(f"Parsed {len(documents)} documents from JSON")
        return documents
        
    except Exception as e:
        logger.error(f"JSON parsing error: {e}")
        raise ValueError(f"Failed to parse JSON: {str(e)}")


async def parse_jsonl(content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse JSONL (JSON Lines) file"""
    documents = []
    try:
        lines = content.decode('utf-8').strip().split('\n')
        
        for line_num, line in enumerate(lines):
            if not line.strip():
                continue
            
            try:
                doc = json.loads(line)
                if isinstance(doc, dict):
                    if 'properties' not in doc:
                        doc['properties'] = {}
                    doc['properties']['line_number'] = line_num
                    doc['properties']['source_file'] = filename
                    doc['properties']['document_type'] = 'jsonl'
                    
                    if 'content' not in doc:
                        content_parts = []
                        for key, value in doc.items():
                            if key != 'properties' and value:
                                content_parts.append(f"{key}: {value}")
                        doc['content'] = " | ".join(content_parts)
                    
                    documents.append(doc)
            except json.JSONDecodeError as je:
                logger.warning(f"Skipping invalid JSON on line {line_num}: {je}")
                continue
        
        if not documents:
            raise ValueError("No valid JSON objects found in JSONL file")
        
        logger.info(f"Parsed {len(documents)} documents from JSONL")
        return documents
        
    except Exception as e:
        logger.error(f"JSONL parsing error: {e}")
        raise ValueError(f"Failed to parse JSONL: {str(e)}")


async def parse_xlsx(content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse Excel file"""
    documents = []
    try:
        df = pd.read_excel(BytesIO(content))
        
        if df.empty:
            raise ValueError("Excel file is empty")
        
        for idx, row in df.iterrows():
            doc = row.to_dict()
            
            # Create content field for embedding
            content_parts = []
            for key, value in doc.items():
                if pd.notna(value):
                    content_parts.append(f"{key}: {value}")
            
            doc['content'] = " | ".join(content_parts)
            doc['properties'] = {
                "row_index": idx,
                "total_rows": len(df),
                "source_file": filename,
                "document_type": "xlsx"
            }
            
            documents.append(doc)
        
        logger.info(f"Parsed {len(documents)} rows from Excel")
        return documents
        
    except Exception as e:
        logger.error(f"Excel parsing error: {e}")
        raise ValueError(f"Failed to parse Excel: {str(e)}")


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def determine_collection(documents: List[Dict[str, Any]]) -> str:
    """Determine which collection documents belong to"""
    if not documents:
        return "NewsArticle"
    
    doc = documents[0]
    keys = set(doc.keys())
    
    # Check for key indicators
    investor_keys = {'focus_areas', 'ticket_size_min', 'ticket_size_max', 'contact_email'}
    deal_keys = {'startup_name', 'funding_amount', 'stage', 'investors', 'valuation'}
    policy_keys = {'scheme_name', 'eligibility', 'benefits', 'target_audience'}
    
    if investor_keys.intersection(keys):
        return "Investor"
    elif deal_keys.intersection(keys):
        return "FundingDeal"
    elif policy_keys.intersection(keys):
        return "PolicyDocument"
    
    return "NewsArticle"


@router.post("/document", response_model=IngestionResponse,
             responses={
                 400: {"description": "Invalid file or parameters"},
                 413: {"description": "File too large"},
                 500: {"description": "Processing error"}
             })
async def ingest_document(
    file: UploadFile = File(...),
    collection: Optional[str] = Query(None, description="Target collection name")
) -> IngestionResponse:
    """
    Ingest a document file (PDF, CSV, JSON, XLSX, JSONL)
    
    Args:
        file: Document file to ingest
        collection: Optional collection name (auto-detected if not provided)
        
    Returns:
        IngestionResponse with document count and status
    """
    try:
        # Validate filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Validate extension
        try:
            ext = validate_file_extension(file.filename)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        
        # Read and validate file size
        content = await file.read()
        try:
            validate_file_size(len(content))
        except ValueError as ve:
            raise HTTPException(status_code=413, detail=str(ve))
        
        logger.info(f"Processing file: {file.filename} ({len(content) / 1024:.1f} KB)")
        
        # Parse based on file type
        try:
            if ext == '.pdf':
                documents = await parse_pdf(content, file.filename)
            elif ext == '.csv':
                documents = await parse_csv(content, file.filename)
            elif ext == '.json':
                documents = await parse_json(content, file.filename)
            elif ext == '.jsonl':
                documents = await parse_jsonl(content, file.filename)
            elif ext == '.xlsx':
                documents = await parse_xlsx(content, file.filename)
            else:
                raise ValueError(f"Unsupported file type: {ext}")
        except ValueError as ve:
            logger.error(f"Parsing error: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        
        if not documents:
            raise HTTPException(status_code=400, detail="No documents extracted from file")
        
        # Determine or validate collection
        target_collection = collection or determine_collection(documents)
        logger.info(f"Using collection: {target_collection}")
        
        # Add to vector store
        try:
            result = await vector_store_service.add_documents(
                collection_name=target_collection,
                documents=documents,
                generate_embeddings=True
            )
            
            success = result.get('success', False)
            added_count = result.get('count', len(documents))
            
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to add documents to vector store"
                )
            
            logger.info(f"Successfully ingested {added_count} documents")
            
            return IngestionResponse(
                success=True,
                documents_added=added_count,
                message=f"Successfully ingested {added_count} documents from {file.filename}",
                metadata={
                    "collection": target_collection,
                    "file_size_kb": len(content) / 1024,
                    "file_type": ext[1:]
                }
            )
            
        except Exception as ve:
            logger.error(f"Vector store error: {ve}")
            raise HTTPException(status_code=500, detail="Failed to store documents")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in document ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error during ingestion")


@router.post("/url", response_model=IngestionResponse,
             responses={
                 400: {"description": "Invalid URL"},
                 500: {"description": "Processing error"}
             })
async def ingest_url(request: URLIngestRequest) -> IngestionResponse:
    """
    Ingest content from a URL
    
    Args:
        request: URLIngestRequest with URL and optional collection
        
    Returns:
        IngestionResponse with status
    """
    try:
        logger.info(f"Ingesting content from URL: {request.url}")
        
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Required dependencies for URL ingestion not available"
            )
        
        # Fetch webpage
        try:
            response = requests.get(request.url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=500, detail="URL request timed out")
        except requests.exceptions.HTTPError as he:
            raise HTTPException(status_code=400, detail=f"HTTP error: {he.response.status_code}")
        except requests.exceptions.RequestException as re:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(re)}")
        
        # Validate content type
        content_type = response.headers.get('content-type', '')
        if 'text/html' not in content_type:
            raise HTTPException(
                status_code=400,
                detail="URL must return HTML content"
            )
        
        # Parse HTML
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse HTML: {str(e)}")
        
        # Extract text
        text = soup.get_text(separator=' ', strip=True)
        if not text or len(text) < 10:
            raise HTTPException(status_code=400, detail="No meaningful content found in URL")
        
        # Extract title
        title = soup.title.string if soup.title else request.url
        
        # Create document
        document = [{
            "content": text,
            "properties": {
                "source": request.url,
                "title": title,
                "document_type": "webpage"
            }
        }]
        
        # Determine collection if not specified
        target_collection = request.collection or "NewsArticle"
        
        # Add to vector store
        try:
            result = await vector_store_service.add_documents(
                collection_name=target_collection,
                documents=document,
                generate_embeddings=True
            )
            
            success = result.get('success', False)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to add URL content to vector store")
            
            logger.info(f"Successfully ingested URL content: {request.url}")
            
            return IngestionResponse(
                success=True,
                documents_added=1,
                message=f"Successfully ingested content from {request.url}",
                metadata={
                    "url": request.url,
                    "title": title,
                    "collection": target_collection,
                    "content_length": len(text)
                }
            )
            
        except Exception as ve:
            logger.error(f"Vector store error: {ve}")
            raise HTTPException(status_code=500, detail="Failed to store URL content")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in URL ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error during URL ingestion")


@router.get("/stats", response_model=IngestionStats)
async def get_ingestion_stats() -> IngestionStats:
    """
    Get ingestion statistics
    
    Returns:
        IngestionStats with summary information
    """
    try:
        logger.info("Fetching ingestion statistics")
        
        # Get stats from vector store
        stats = await vector_store_service.get_stats()
        
        return IngestionStats(
            total_documents=stats.get('total_documents', 0),
            total_size_mb=stats.get('total_size_mb', 0.0),
            collections=stats.get('collections', {})
        )
        
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching statistics")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for ingestion service
    
    Returns:
        Health status information
    """
    try:
        return {
            "status": "healthy",
            "service": "ingest",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

