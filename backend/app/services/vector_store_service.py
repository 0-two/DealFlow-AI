"""
Vector Store Service for managing vector database operations with Weaviate
"""
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from typing import List, Dict, Optional, Any, Tuple
import logging
from app.config.settings import settings
from app.services.embedding_service import embedding_service
from app.utils.logger import setup_logger
import time
import asyncio
from collections import OrderedDict

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

            # Simple in-memory search cache
            self._search_cache: "OrderedDict[str, Tuple[float, List[Dict]] ]" = OrderedDict()
            self._search_cache_lock = asyncio.Lock()
            
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
                        Property(name="investment_thesis", data_type=DataType.TEXT),
                        Property(name="investment_criteria", data_type=DataType.TEXT),
                        Property(name="stages", data_type=DataType.TEXT_ARRAY),
                        Property(name="geographies", data_type=DataType.TEXT_ARRAY),
                        Property(name="created_date", data_type=DataType.DATE),
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
    
    def recreate_collection(self, collection_name: str) -> bool:
        """
        Delete and recreate a collection with updated schema.
        WARNING: This will delete all existing data in the collection!
        
        Args:
            collection_name: Name of the collection to recreate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete if exists
            if self.client.collections.exists(collection_name):
                logger.warning(f"Deleting collection {collection_name} for recreation")
                self.client.collections.delete(collection_name)
                logger.info(f"Deleted collection {collection_name}")
            
            # Reinitialize collections (will recreate the deleted one)
            self.initialize_collections()
            
            logger.info(f"Successfully recreated collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error recreating collection {collection_name}: {str(e)}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a collection including property count"""
        try:
            if not self.client.collections.exists(collection_name):
                return None
            
            collection = self.client.collections.get(collection_name)
            config = collection.config.get()
            
            return {
                "name": collection_name,
                "properties": [p.name for p in config.properties],
                "property_count": len(config.properties)
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return None
    
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
                            # Remove vector and internal fields from properties
                            doc_properties = {
                                k: v for k, v in doc.items() 
                                if k != "vector" and not k.startswith("_") and v is not None
                            }
                            
                            # Log the properties being inserted for debugging
                            logger.debug(
                                f"Inserting document {idx} with properties: {list(doc_properties.keys())}"
                            )
                            
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
                            logger.error(f"Document properties were: {doc_properties}")
                            continue
                
                # Check for batch errors
                if hasattr(batch, 'failed_objects') and batch.failed_objects:
                    for failed_obj in batch.failed_objects:
                        logger.error(f"Failed object in batch: {failed_obj}")
                        failed_count += 1
                        inserted_count -= 1
                
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
            # Cache lookup
            if settings.CACHE_ENABLED:
                cache_key = f"{collection_name}|{limit}|{query.strip()}|{str(filters) if filters else ''}"
                now = time.time()
                async with self._search_cache_lock:
                    if cache_key in self._search_cache:
                        ts, value = self._search_cache[cache_key]
                        if now - ts <= settings.SEARCH_CACHE_TTL_SECONDS:
                            # move to end (LRU)
                            self._search_cache.move_to_end(cache_key)
                            logger.debug("Search cache hit for %s", collection_name)
                            return value
                        else:
                            # expired
                            self._search_cache.pop(cache_key, None)
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
                from weaviate.classes.query import Filter
                filter_conditions = []
                
                # Build filter conditions based on provided filters
                if 'sector' in filters and filters['sector']:
                    filter_conditions.append(
                        Filter.by_property("focus_areas").contains_any([filters['sector']])
                    )
                
                if 'location' in filters and filters['location']:
                    filter_conditions.append(
                        Filter.by_property("location").like(f"*{filters['location']}*")
                    )
                
                if 'stage' in filters and filters['stage']:
                    filter_conditions.append(
                        Filter.by_property("stages").contains_any([filters['stage']])
                    )
                
                if 'investor_type' in filters and filters['investor_type']:
                    filter_conditions.append(
                        Filter.by_property("type").like(f"*{filters['investor_type']}*")
                    )
                
                # Combine filters with AND logic
                if filter_conditions:
                    if len(filter_conditions) == 1:
                        where_filter = filter_conditions[0]
                    else:
                        where_filter = filter_conditions[0]
                        for condition in filter_conditions[1:]:
                            where_filter = where_filter & condition
                    
                    logger.debug(f"Applied filters: {filters}")
            
            # Perform hybrid search
            try:
                if where_filter:
                    response = collection.query.hybrid(
                        query=query,
                        vector=query_vector,
                        limit=limit,
                        filters=where_filter,
                        return_metadata=['score']
                    )
                else:
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
                # Cache set
                if settings.CACHE_ENABLED:
                    async with self._search_cache_lock:
                        self._search_cache[cache_key] = (time.time(), results)
                        self._search_cache.move_to_end(cache_key)
                        # evict if oversized
                        while len(self._search_cache) > settings.SEARCH_CACHE_MAX_ENTRIES:
                            self._search_cache.popitem(last=False)
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
