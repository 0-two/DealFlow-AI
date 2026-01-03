"""
Embedding Service for generating vector embeddings using Google Generative AI
"""
import google.generativeai as genai
from typing import List, Optional
import logging
import asyncio
import time
from collections import deque
from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    """Simple rate limiter using token bucket algorithm"""
    
    def __init__(self, max_requests: int = 60, time_window: float = 60.0):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request"""
        async with self.lock:
            now = time.time()
            
            # Remove requests outside the time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # Check if we've exceeded the rate limit
            if len(self.requests) >= self.max_requests:
                # Calculate wait time until oldest request expires
                wait_time = self.time_window - (now - self.requests[0])
                logger.debug(f"Rate limit reached. Waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                # Clean up again after waiting
                while self.requests and self.requests[0] < time.time() - self.time_window:
                    self.requests.popleft()
            
            # Add current request timestamp
            self.requests.append(time.time())


class EmbeddingService:
    """Service for generating text embeddings using Google Generative AI"""
    
    def __init__(self):
        """Initialize embedding service"""
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not configured in settings")
        
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        
        # Rate limiting: 60 requests per minute (conservative limit)
        self.rate_limiter = RateLimiter(max_requests=60, time_window=60.0)
        
        # Semaphore to limit concurrent requests
        self.semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
        
        # Batch size for processing
        self.batch_size = 100
        
        logger.info(f"EmbeddingService initialized with model: {self.model}")
    
    async def _generate_single_embedding(
        self,
        text: str,
        task_type: str = "retrieval_document"
    ) -> List[float]:
        """
        Generate embedding for a single text with rate limiting and error handling
        
        Args:
            text: Text to embed
            task_type: Task type ("retrieval_document" or "retrieval_query")
            
        Returns:
            Embedding vector
            
        Raises:
            ValueError: If text is empty
            Exception: On API errors
        """
        if not text or not text.strip():
            raise ValueError("Empty text provided for embedding")
        
        # Rate limiting
        await self.rate_limiter.acquire()
        
        # Acquire semaphore for concurrent request limiting
        async with self.semaphore:
            try:
                logger.debug(
                    f"Generating embedding for text (length: {len(text)}, "
                    f"task_type: {task_type})"
                )
                start_time = time.time()
                
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: genai.embed_content(
                        model=self.model,
                        content=text,
                        task_type=task_type
                    )
                )
                
                processing_time = time.time() - start_time
                
                # Validate response
                if not result or 'embedding' not in result:
                    raise ValueError(f"Invalid response from embedding API: {result}")
                
                embedding = result['embedding']
                
                if not embedding or not isinstance(embedding, list):
                    raise ValueError(f"Invalid embedding format: {type(embedding)}")
                
                logger.debug(
                    f"Embedding generated successfully in {processing_time:.3f}s "
                    f"(dimension: {len(embedding)})"
                )
                
                return embedding
                
            except genai.types.StopCandidateException as e:
                logger.error(f"API stop candidate error: {str(e)}")
                raise Exception(f"Embedding API error: {str(e)}")
            except genai.types.BlockedPromptException as e:
                logger.error(f"API blocked prompt error: {str(e)}")
                raise ValueError(f"Content blocked by API: {str(e)}")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error generating embedding: {error_msg}")
                
                # Check for rate limit errors
                if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    logger.warning("Rate limit error detected, waiting before retry")
                    await asyncio.sleep(2)  # Wait before retrying
                    raise Exception("Rate limit exceeded. Please try again later.")
                
                raise Exception(f"Embedding generation failed: {error_msg}")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for list of texts with batch processing
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            ValueError: If texts list is empty
            Exception: On API errors
        """
        if not texts:
            logger.warning("Empty texts list provided for embedding")
            return []
        
        if not isinstance(texts, list):
            raise ValueError(f"Expected list of texts, got {type(texts)}")
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        start_time = time.time()
        
        embeddings = []
        
        try:
            # Process in batches
            total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
            
            for batch_idx in range(0, len(texts), self.batch_size):
                batch = texts[batch_idx:batch_idx + self.batch_size]
                batch_num = (batch_idx // self.batch_size) + 1
                
                logger.debug(
                    f"Processing batch {batch_num}/{total_batches} "
                    f"({len(batch)} texts)"
                )
                
                # Generate embeddings for batch concurrently
                batch_embeddings = await asyncio.gather(
                    *[self._generate_single_embedding(text, "retrieval_document") for text in batch],
                    return_exceptions=True
                )
                
                # Handle results and exceptions
                for idx, result in enumerate(batch_embeddings):
                    if isinstance(result, Exception):
                        logger.error(
                            f"Error embedding text {batch_idx + idx}: {str(result)}"
                        )
                        # Re-raise if it's a critical error
                        if isinstance(result, ValueError):
                            raise result
                        # For other errors, you might want to use a default embedding
                        # or skip the text. Here we'll raise to be explicit.
                        raise Exception(f"Failed to generate embedding for text {batch_idx + idx}: {str(result)}")
                    embeddings.append(result)
                
                logger.debug(f"Batch {batch_num}/{total_batches} completed")
            
            total_time = time.time() - start_time
            logger.info(
                f"Generated {len(embeddings)} embeddings in {total_time:.3f}s "
                f"({len(embeddings)/total_time:.2f} embeddings/sec)"
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {str(e)}", exc_info=True)
            raise
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for query text
        
        Args:
            query: Query text to embed
            
        Returns:
            Query embedding vector
            
        Raises:
            ValueError: If query is empty
            Exception: On API errors
        """
        if not query or not query.strip():
            raise ValueError("Empty query provided for embedding")
        
        logger.info(f"Generating query embedding (length: {len(query)})")
        start_time = time.time()
        
        try:
            embedding = await self._generate_single_embedding(query, "retrieval_query")
            
            processing_time = time.time() - start_time
            logger.info(
                f"Query embedding generated in {processing_time:.3f}s "
                f"(dimension: {len(embedding)})"
            )
            
            return embedding
            
        except Exception as e:
            logger.error(f"Query embedding error: {str(e)}")
            raise


# Singleton instance
embedding_service = EmbeddingService()
