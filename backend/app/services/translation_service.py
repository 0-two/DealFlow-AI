"""
Bhashini Translation Service for Indic Language Translation
"""
import requests
import logging
import asyncio
import time
from typing import Optional, Dict
from functools import wraps
from app.config.settings import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}. "
                            f"Retrying in {delay:.2f}s. Error: {str(e)}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {func.__name__}. "
                            f"Final error: {str(e)}"
                        )
                except Exception as e:
                    # Don't retry for non-network errors
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                    raise
            
            # If all retries failed, raise the last exception
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class BhashiniTranslationService:
    """Service for translating text using Bhashini API"""
    
    def __init__(self):
        self.base_url = "https://dhruvaapi.bhashini.gov.in/services/inference/pipeline"
        self.config_url = "https://meityauth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
        self.api_key = settings.BHASHINI_API_KEY
        self.user_id = settings.BHASHINI_USER_ID
        self.ulca_api_key = settings.BHASHINI_API_KEY_ULC
        
        # Request timeout settings
        self.timeout = 30  # seconds
        
        # Language code mapping
        self.lang_codes = {
            "hindi": "hi",
            "tamil": "ta",
            "telugu": "te",
            "kannada": "kn",
            "bengali": "bn",
            "marathi": "mr",
            "gujarati": "gu",
            "malayalam": "ml",
            "punjabi": "pa",
            "english": "en"
        }
        
        # Translation cache (simple in-memory cache)
        # In production, consider using Redis or similar
        self.cache: Dict[str, str] = {}
        self.cache_max_size = 1000  # Maximum cache entries
        
        logger.info("BhashiniTranslationService initialized")
    
    def _get_pipeline_config(self, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Get Bhashini pipeline configuration (synchronous helper)
        
        Args:
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Pipeline configuration dict or None on error
        """
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang
                        }
                    }
                }
            ],
            "pipelineRequestConfig": {
                "pipelineId": "64392f96daac500b55c543cd"
            }
        }
        
        headers = {
            "userID": self.user_id,
            "ulcaApiKey": self.ulca_api_key,
            "Content-Type": "application/json"
        }
        
        try:
            logger.debug(
                f"Requesting pipeline config for {source_lang} -> {target_lang}"
            )
            start_time = time.time()
            
            response = requests.post(
                self.config_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            response.raise_for_status()
            
            config = response.json()
            logger.info(
                f"Pipeline config retrieved successfully in {response_time:.3f}s "
                f"for {source_lang} -> {target_lang}"
            )
            return config
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout getting pipeline config for {source_lang} -> {target_lang}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP error getting pipeline config: {e.response.status_code} - "
                f"{e.response.text[:200]}"
            )
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting pipeline config: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting pipeline config: {str(e)}", exc_info=True)
            return None
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def _translate_with_retry(
        self,
        text: str,
        source_code: str,
        target_code: str,
        service_id: str,
        callback_url: str,
        auth_token: str
    ) -> str:
        """
        Perform translation request with retry logic
        
        Args:
            text: Text to translate
            source_code: Source language code
            target_code: Target language code
            service_id: Service ID from pipeline config
            callback_url: Callback URL from pipeline config
            auth_token: Authorization token
            
        Returns:
            Translated text
            
        Raises:
            requests.exceptions.RequestException: On API errors
        """
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_code,
                            "targetLanguage": target_code
                        },
                        "serviceId": service_id
                    }
                }
            ],
            "inputData": {
                "input": [{"source": text}]
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_token
        }
        
        logger.debug(
            f"Translating text (length: {len(text)}) from {source_code} to {target_code}"
        )
        start_time = time.time()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(
                callback_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
        )
        
        response_time = time.time() - start_time
        response.raise_for_status()
        result = response.json()
        
        # Extract translated text
        translated_text = result["pipelineResponse"][0]["output"][0]["target"]
        
        logger.info(
            f"Translation completed in {response_time:.3f}s: "
            f"{source_code} -> {target_code} (text length: {len(text)} -> {len(translated_text)})"
        )
        
        return translated_text
    
    def _manage_cache(self, cache_key: str, value: Optional[str] = None) -> Optional[str]:
        """
        Manage translation cache
        
        Args:
            cache_key: Cache key
            value: Optional value to store
            
        Returns:
            Cached value if retrieving, None if storing
        """
        # If cache is too large, clear oldest entries (simple FIFO)
        if len(self.cache) >= self.cache_max_size and cache_key not in self.cache:
            # Remove first 10% of entries (simple cleanup)
            keys_to_remove = list(self.cache.keys())[:self.cache_max_size // 10]
            for key in keys_to_remove:
                del self.cache[key]
            logger.debug(f"Cache cleaned: removed {len(keys_to_remove)} entries")
        
        if value is not None:
            self.cache[cache_key] = value
            logger.debug(f"Cached translation for key: {cache_key[:50]}...")
            return None
        else:
            return self.cache.get(cache_key)
    
    async def get_pipeline_config(self, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Get Bhashini pipeline configuration (async wrapper)
        
        Args:
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Pipeline configuration dict or None on error
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._get_pipeline_config,
            source_lang,
            target_lang
        )
    
    async def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "hi"
    ) -> Optional[str]:
        """
        Translate text using Bhashini API
        
        Args:
            text: Text to translate
            source_lang: Source language (name or code)
            target_lang: Target language (name or code)
            
        Returns:
            Translated text or original text on error
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for translation")
            return text
        
        # Check cache
        cache_key = f"{text}_{source_lang}_{target_lang}"
        cached_result = self._manage_cache(cache_key)
        if cached_result:
            logger.debug("Translation cache hit")
            return cached_result
        
        try:
            # Get source and target codes
            source_code = self.lang_codes.get(source_lang.lower(), source_lang)
            target_code = self.lang_codes.get(target_lang.lower(), target_lang)
            
            logger.info(
                f"Starting translation: {source_lang} ({source_code}) -> "
                f"{target_lang} ({target_code}), text length: {len(text)}"
            )
            
            # If same language, return as is
            if source_code == target_code:
                logger.debug(f"Source and target languages are the same ({source_code})")
                return text
            
            # Get pipeline config
            config = await self.get_pipeline_config(source_code, target_code)
            if not config:
                logger.error("Failed to get pipeline config, returning original text")
                return text
            
            # Extract service ID and callback URL
            try:
                pipeline = config["pipelineResponseConfig"][0]
                service_id = pipeline["config"][0]["serviceId"]
                callback_url = pipeline["config"][0]["callbackUrl"]
                auth_token = config.get("authorization", "")
                
                if not auth_token:
                    logger.warning("No authorization token in pipeline config")
                    
            except (KeyError, IndexError) as e:
                logger.error(f"Error parsing pipeline config: {str(e)}")
                logger.debug(f"Config structure: {config}")
                return text
            
            # Perform translation with retry logic
            translated_text = await self._translate_with_retry(
                text=text,
                source_code=source_code,
                target_code=target_code,
                service_id=service_id,
                callback_url=callback_url,
                auth_token=auth_token
            )
            
            # Cache the result
            self._manage_cache(cache_key, translated_text)
            
            return translated_text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Translation API error: {str(e)}")
            return text  # Return original on error
        except KeyError as e:
            logger.error(f"Error parsing translation response: {str(e)}")
            return text
        except Exception as e:
            logger.error(f"Unexpected error during translation: {str(e)}", exc_info=True)
            return text  # Return original on error
    
    async def detect_language(self, text: str) -> str:
        """
        Detect language of input text using Unicode range heuristics
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected language code
        """
        if not text or not text.strip():
            logger.debug("Empty text provided for language detection")
            return "en"
        
        logger.debug(f"Detecting language for text (length: {len(text)})")
        
        # Check for Devanagari (Hindi, Marathi, etc.)
        if any('\u0900' <= char <= '\u097F' for char in text):
            logger.debug("Detected language: Hindi (Devanagari script)")
            return "hi"
        # Check for Tamil
        elif any('\u0B80' <= char <= '\u0BFF' for char in text):
            logger.debug("Detected language: Tamil")
            return "ta"
        # Check for Telugu
        elif any('\u0C00' <= char <= '\u0C7F' for char in text):
            logger.debug("Detected language: Telugu")
            return "te"
        # Check for Kannada
        elif any('\u0C80' <= char <= '\u0CFF' for char in text):
            logger.debug("Detected language: Kannada")
            return "kn"
        # Check for Bengali
        elif any('\u0980' <= char <= '\u09FF' for char in text):
            logger.debug("Detected language: Bengali")
            return "bn"
        # Check for Gujarati
        elif any('\u0A80' <= char <= '\u0AFF' for char in text):
            logger.debug("Detected language: Gujarati")
            return "gu"
        # Check for Malayalam
        elif any('\u0D00' <= char <= '\u0D7F' for char in text):
            logger.debug("Detected language: Malayalam")
            return "ml"
        # Check for Gurmukhi (Punjabi)
        elif any('\u0A00' <= char <= '\u0A7F' for char in text):
            logger.debug("Detected language: Punjabi")
            return "pa"
        else:
            logger.debug("Detected language: English (default)")
            return "en"  # Default to English


# Create singleton instance
translation_service = BhashiniTranslationService()
