"""
Vector Store Service for managing vector database operations with Weaviate
"""
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from typing import List, Dict, Optional, Any
import logging
from app.config.settings import settings
from app.services.embedding_service import embedding_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class VectorStoreService:
    """Service for managing vector database operations with Weaviate"""
    
    def __init__(self):
        """Initialize Weaviate client and collections"""
        try:
            if not settings.WEAVIATE_URL:
                raise ValueError("WEAVIATE_URL not configured in settings")
            if not settings.WEAVIATE_API_KEY:
                raise ValueError("WEAVIATE_API_KEY not configured in settings")
            
            logger.info(f"Connecting to Weaviate at {settings.WEAVIATE_URL}")
            
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=settings.WEAVIATE_URL,
                auth_credentials=weaviate.auth.AuthApiKey(settings.WEAVIATE_API_KEY)
            )
            
            logger.info("Successfully connected to Weaviate")
            self.initialize_collections()
            
        except weaviate.exceptions.WeaviateBaseError as e:
            logger.error(f"Weaviate connection error: {str(e)}")
            raise Exception(f"Failed to connect to Weaviate: {str(e)}")
        except Exception as e:
            logger.error(f"Error initializing VectorStoreService: {str(e)}", exc_info=True)
            raise
    
    def initialize_collections(self):
        """Create Weaviate collections/schemas"""
        try:
            logger.info("Initializing Weaviate collections")
            collections_created = []
            collections_existing = []
            
            # Investor Collection
            if not self.client.collections.exists("Investor"):
                self.client.collections.create(
                    name="Investor",
                    properties=[
                        Property(name="name", data_type=DataType.TEXT),
                        Property(name="type", data_type=DataType.TEXT),
                        Property(name="focus_areas", data_type=DataType.TEXT_ARRAY),
                        Property(name="location", data_type=DataType.TEXT),
                        Property(name="ticket_size_min", data_type=DataType.NUMBER),
                        Property(name="ticket_size_max", data_type=DataType.NUMBER),
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="contact_email", data_type=DataType.TEXT),
                        Property(name="website", data_type=DataType.TEXT),
                        Property(name="portfolio", data_type=DataType.TEXT_ARRAY),
                    ],
                    vectorizer_config=Configure.Vectorizer.none(),  # We'll provide vectors
                )
                collections_created.append("Investor")
                logger.info("Created Investor collection")
            else:
                collections_existing.append("Investor")
                logger.debug("Investor collection already exists")
            
            # Funding Deals Collection
            if not self.client.collections.exists("FundingDeal"):
                self.client.collections.create(
                    name="FundingDeal",
                    properties=[
                        Property(name="startup_name", data_type=DataType.TEXT),
                        Property(name="amount", data_type=DataType.NUMBER),
                        Property(name="currency", data_type=DataType.TEXT),
                        Property(name="stage", data_type=DataType.TEXT),
                        Property(name="sector", data_type=DataType.TEXT),
                        Property(name="investors", data_type=DataType.TEXT_ARRAY),
                        Property(name="date", data_type=DataType.DATE),
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="source", data_type=DataType.TEXT),
                    ],
                    vectorizer_config=Configure.Vectorizer.none(),
                )
                collections_created.append("FundingDeal")
                logger.info("Created FundingDeal collection")
            else:
                collections_existing.append("FundingDeal")
                logger.debug("FundingDeal collection already exists")
            
            # Policy Documents Collection
            if not self.client.collections.exists("PolicyDocument"):
                self.client.collections.create(
                    name="PolicyDocument",
                    properties=[
                        Property(name="scheme_name", data_type=DataType.TEXT),
                        Property(name="authority", data_type=DataType.TEXT),
                        Property(name="sector", data_type=DataType.TEXT),
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="eligibility", data_type=DataType.TEXT),
                        Property(name="benefits", data_type=DataType.TEXT),
                        Property(name="deadline", data_type=DataType.DATE),
                        Property(name="source_url", data_type=DataType.TEXT),
                    ],
                    vectorizer_config=Configure.Vectorizer.none(),
                )
                collections_created.append("PolicyDocument")
                logger.info("Created PolicyDocument collection")
            else:
                collections_existing.append("PolicyDocument")
                logger.debug("PolicyDocument collection already exists")
            
            # News Articles Collection
            if not self.client.collections.exists("NewsArticle"):
                self.client.collections.create(
                    name="NewsArticle",
                    properties=[
                        Property(name="title", data_type=DataType.TEXT),
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="source", data_type=DataType.TEXT),
                        Property(name="url", data_type=DataType.TEXT),
                        Property(name="published_date", data_type=DataType.DATE),
                        Property(name="sector", data_type=DataType.TEXT),
                    ],
                    vectorizer_config=Configure.Vectorizer.none(),
                )
                collections_created.append("NewsArticle")
                logger.info("Created NewsArticle collection")
            else:
                collections_existing.append("NewsArticle")
                logger.debug("NewsArticle collection already exists")
            
            # Startup Collection
            if not self.client.collections.exists("Startup"):
                self.client.collections.create(
                    name="Startup",
                    properties=[
                        Property(name="startup_name", data_type=DataType.TEXT),
                        Property(name="founder_name", data_type=DataType.TEXT),
                        Property(name="sector", data_type=DataType.TEXT),
                        Property(name="stage", data_type=DataType.TEXT),
                        Property(name="location", data_type=DataType.TEXT),
                        Property(name="funding_amount", data_type=DataType.NUMBER),
                        Property(name="description", data_type=DataType.TEXT),
                        Property(name="problem_statement", data_type=DataType.TEXT),
                        Property(name="solution", data_type=DataType.TEXT),
                        Property(name="market_size", data_type=DataType.TEXT),
                        Property(name="business_model", data_type=DataType.TEXT),
                        Property(name="traction", data_type=DataType.TEXT),
                        Property(name="team_size", data_type=DataType.NUMBER),
                        Property(name="revenue", data_type=DataType.NUMBER),
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="pitch_deck_url", data_type=DataType.TEXT),
                        Property(name="contact_email", data_type=DataType.TEXT),
                        Property(name="website", data_type=DataType.TEXT),
                        Property(name="created_date", data_type=DataType.DATE),
                    ],
                    vectorizer_config=Configure.Vectorizer.none(),
                )
                collections_created.append("Startup")
                logger.info("Created Startup collection")
            else:
                collections_existing.append("Startup")
                logger.debug("Startup collection already exists")
            
            if collections_created:
                logger.info(f"Weaviate collections initialized successfully. Created: {collections_created}")
            if collections_existing:
                logger.info(f"Collections already exist: {collections_existing}")
                
        except weaviate.exceptions.SchemaValidationError as e:
            logger.error(f"Schema validation error: {str(e)}")
            raise Exception(f"Schema validation failed: {str(e)}")
        except weaviate.exceptions.WeaviateBaseError as e:
            logger.error(f"Weaviate error initializing collections: {str(e)}")
            raise Exception(f"Failed to initialize collections: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error initializing collections: {str(e)}", exc_info=True)
            raise
    
    async def add_documents(
        self,
        collection_name: str,
        documents: List[Dict],
        generate_embeddings: bool = True
    ) -> bool:
        """
        Add documents to collection
        
        Args:
            collection_name: Name of the collection
            documents: List of document dictionaries
            generate_embeddings: Whether to generate embeddings (default: True)
            
        Returns:
            True if successful, False otherwise
        """
        if not documents:
            logger.warning(f"Empty documents list provided for collection {collection_name}")
            return False
        
        if not collection_name:
            logger.error("Collection name is required")
            return False
        
        try:
            # Check if collection exists
            if not self.client.collections.exists(collection_name):
                logger.error(f"Collection {collection_name} does not exist")
                return False
            
            collection = self.client.collections.get(collection_name)
            logger.info(
                f"Adding {len(documents)} documents to collection {collection_name} "
                f"(generate_embeddings={generate_embeddings})"
            )
            
            # Generate embeddings if needed
            embeddings = None
            if generate_embeddings:
                try:
                    contents = [doc.get("content", "") for doc in documents]
                    if not all(contents):
                        logger.warning("Some documents have empty content, proceeding anyway")
                    
                    logger.debug(f"Generating embeddings for {len(documents)} documents")
                    embeddings = await embedding_service.generate_embeddings(contents)
                    
                    if len(embeddings) != len(documents):
                        logger.error(
                            f"Embedding count mismatch: {len(embeddings)} embeddings "
                            f"for {len(documents)} documents"
                        )
                        return False
                    
                    logger.debug(f"Generated {len(embeddings)} embeddings successfully")
                except Exception as e:
                    logger.error(f"Error generating embeddings: {str(e)}")
                    return False
            else:
                # Extract vectors from documents
                embeddings = [doc.get("vector") for doc in documents]
                if not all(embeddings):
                    logger.error("Some documents are missing vector embeddings")
                    return False
            
            # Batch insert
            inserted_count = 0
            failed_count = 0
            
            try:
                with collection.batch.dynamic() as batch:
                    for idx, (doc, vector) in enumerate(zip(documents, embeddings)):
                        try:
                            # Remove vector from properties if present
                            doc_properties = {k: v for k, v in doc.items() if k != "vector"}
                            
                            batch.add_object(
                                properties=doc_properties,
                                vector=vector
                            )
                            inserted_count += 1
                        except Exception as e:
                            failed_count += 1
                            logger.error(
                                f"Error adding document {idx} to batch: {str(e)}"
                            )
                            continue
                
                logger.info(
                    f"Batch insert completed for {collection_name}: "
                    f"{inserted_count} successful, {failed_count} failed"
                )
                
                return inserted_count > 0
                
            except weaviate.exceptions.WeaviateBaseError as e:
                logger.error(f"Weaviate error during batch insert: {str(e)}")
                return False
            
        except weaviate.exceptions.WeaviateBaseError as e:
            logger.error(f"Weaviate error adding documents: {str(e)}")
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error adding documents to {collection_name}: {str(e)}",
                exc_info=True
            )
            return False
    
    async def hybrid_search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Perform hybrid search (vector + keyword)
        
        Args:
            collection_name: Name of the collection to search
            query: Search query text
            limit: Maximum number of results to return
            filters: Optional filters (where clauses)
            
        Returns:
            List of search results with properties and scores
        """
        if not query or not query.strip():
            logger.warning("Empty query provided for hybrid search")
            return []
        
        if not collection_name:
            logger.error("Collection name is required for search")
            return []
        
        try:
            # Check if collection exists
            if not self.client.collections.exists(collection_name):
                logger.error(f"Collection {collection_name} does not exist")
                return []
            
            collection = self.client.collections.get(collection_name)
            logger.info(
                f"Performing hybrid search in {collection_name}: "
                f"query='{query[:50]}...', limit={limit}"
            )
            
            # Generate query embedding
            try:
                query_vector = await embedding_service.generate_query_embedding(query)
                logger.debug(f"Generated query embedding (dimension: {len(query_vector)})")
            except Exception as e:
                logger.error(f"Error generating query embedding: {str(e)}")
                return []
            
            # Build filter if provided
            where_filter = None
            if filters:
                # TODO: Implement filter logic based on schema
                # This is a placeholder - implement based on your filter requirements
                logger.debug(f"Filters provided: {filters} (not yet implemented)")
                # Example: where_filter = Filter.by_property("sector").equal("Technology")
            
            # Perform hybrid search
            try:
                response = collection.query.hybrid(
                    query=query,
                    vector=query_vector,
                    limit=limit,
                    return_metadata=['score']
                )
                
                results = []
                for item in response.objects:
                    try:
                        results.append({
                            "uuid": str(item.uuid),
                            "properties": item.properties,
                            "score": item.metadata.score if item.metadata else 0.0
                        })
                    except Exception as e:
                        logger.warning(f"Error processing search result: {str(e)}")
                        continue
                
                logger.info(
                    f"Hybrid search completed: found {len(results)} results "
                    f"for query in {collection_name}"
                )
                
                return results
                
            except weaviate.exceptions.WeaviateQueryError as e:
                logger.error(f"Weaviate query error: {str(e)}")
                return []
            
        except weaviate.exceptions.WeaviateBaseError as e:
            logger.error(f"Weaviate error during hybrid search: {str(e)}")
            return []
        except Exception as e:
            logger.error(
                f"Unexpected error during hybrid search: {str(e)}",
                exc_info=True
            )
            return []
    
    def close(self):
        """Close Weaviate connection"""
        try:
            if hasattr(self, 'client') and self.client:
                self.client.close()
                logger.info("Weaviate connection closed")
        except Exception as e:
            logger.error(f"Error closing Weaviate connection: {str(e)}")
    
    def __del__(self):
        """Destructor to ensure connection is closed"""
        try:
            self.close()
        except Exception:
            pass


# Singleton instance
# Note: For production, consider using lazy initialization or connection pooling
try:
    vector_store_service = VectorStoreService()
except Exception as e:
    logger.error(f"Failed to initialize vector_store_service singleton: {str(e)}")
    vector_store_service = None
