import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from huggingface_hub import login
import logging
from typing import Optional, Dict
import os
from functools import lru_cache
from app.config.settings import settings

logger = logging.getLogger(__name__)

class IndicTrans2Service:
    """
    High-quality translation service using IndicTrans2 from AI4Bharat
    Supports all major Indian languages with state-of-the-art quality
    """
    
    def __init__(self):
        # Authenticate with Hugging Face
        self._authenticate_huggingface()
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Language mappings for IndicTrans2
        self.lang_codes = {
            "hindi": "hin_Deva",
            "tamil": "tam_Taml",
            "telugu": "tel_Telu",
            "kannada": "kan_Knda",
            "bengali": "ben_Beng",
            "marathi": "mar_Deva",
            "gujarati": "guj_Gujr",
            "malayalam": "mal_Mlym",
            "punjabi": "pan_Guru",
            "odia": "ory_Orya",
            "assamese": "asm_Beng",
            "english": "eng_Latn"
        }
        
        # Reverse mapping
        self.code_to_lang = {v: k for k, v in self.lang_codes.items()}
        
        # Model paths
        self.en_indic_model_name = "ai4bharat/indictrans2-en-indic-1B"
        self.indic_en_model_name = "ai4bharat/indictrans2-indic-en-1B"
        
        # Lazy load models (only when needed)
        self.en_indic_model = None
        self.indic_en_model = None
        self.en_indic_tokenizer = None
        self.indic_en_tokenizer = None
        self.ip = None
        
        # Translation cache
        self.cache: Dict[str, str] = {}
        
        logger.info("IndicTrans2 service initialized (models will load on first use)")
    
    def _authenticate_huggingface(self):
        """Authenticate with Hugging Face using token from settings"""
        try:
            if settings.HUGGINGFACE_HUB_TOKEN:
                logger.info("🔑 Authenticating with Hugging Face...")
                login(token=settings.HUGGINGFACE_HUB_TOKEN)
                logger.info("✅ Hugging Face authentication successful")
            else:
                logger.warning("⚠️ No HUGGINGFACE_HUB_TOKEN found in settings")
                logger.warning("🔑 Please add HUGGINGFACE_HUB_TOKEN to your .env file")
        except Exception as e:
            logger.error(f"❌ Hugging Face authentication failed: {e}")
            logger.warning("⚠️ IndicTrans2 models may not work without authentication")
    
    def _load_en_to_indic_model(self):
        """Lazy load English to Indic model"""
        if self.en_indic_model is None:
            logger.info("Loading English to Indic translation model...")
            try:
                self.en_indic_tokenizer = AutoTokenizer.from_pretrained(
                    self.en_indic_model_name,
                    trust_remote_code=True
                )
                self.en_indic_model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.en_indic_model_name,
                    trust_remote_code=True
                )
                self.en_indic_model.to(self.device)
                self.en_indic_model.eval()
                
                # Initialize processor
                if self.ip is None:
                    from IndicTransToolkit import IndicProcessor
                    self.ip = IndicProcessor(inference=True)
                
                logger.info("✅ English to Indic model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading English to Indic model: {e}")
                raise
    
    def _load_indic_to_en_model(self):
        """Lazy load Indic to English model"""
        if self.indic_en_model is None:
            logger.info("Loading Indic to English translation model...")
            try:
                self.indic_en_tokenizer = AutoTokenizer.from_pretrained(
                    self.indic_en_model_name,
                    trust_remote_code=True
                )
                self.indic_en_model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.indic_en_model_name,
                    trust_remote_code=True
                )
                self.indic_en_model.to(self.device)
                self.indic_en_model.eval()
                
                # Initialize processor
                if self.ip is None:
                    from IndicTransToolkit import IndicProcessor
                    self.ip = IndicProcessor(inference=True)
                
                logger.info("✅ Indic to English model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading Indic to English model: {e}")
                raise
    
    async def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "hi"
    ) -> Optional[str]:
        """
        Translate text between English and Indic languages
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en', 'hi')
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        try:
            # Check cache
            cache_key = f"{text[:100]}_{source_lang}_{target_lang}"
            if cache_key in self.cache:
                logger.info("Translation retrieved from cache")
                return self.cache[cache_key]
            
            # Get proper language codes
            source_code = self.lang_codes.get(source_lang.lower(), source_lang)
            target_code = self.lang_codes.get(target_lang.lower(), target_lang)
            
            # If same language, return as is
            if source_code == target_code:
                return text
            
            # Handle empty or very short text
            if not text or len(text.strip()) < 2:
                return text
            
            # Determine translation direction
            is_en_to_indic = source_code == "eng_Latn"
            is_indic_to_en = target_code == "eng_Latn"
            
            if is_en_to_indic:
                # English to Indic
                self._load_en_to_indic_model()
                translated = self._translate_en_to_indic(text, target_code)
            elif is_indic_to_en:
                # Indic to English
                self._load_indic_to_en_model()
                translated = self._translate_indic_to_en(text, source_code)
            else:
                # Indic to Indic (via English pivot)
                logger.info("Indic-to-Indic translation via English pivot")
                self._load_indic_to_en_model()
                english_text = self._translate_indic_to_en(text, source_code)
                self._load_en_to_indic_model()
                translated = self._translate_en_to_indic(english_text, target_code)
            
            # Cache result
            self.cache[cache_key] = translated
            
            # Limit cache size
            if len(self.cache) > 1000:
                # Remove oldest 200 entries
                for _ in range(200):
                    self.cache.pop(next(iter(self.cache)))
            
            return translated
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text  # Return original on error
    
    def _translate_en_to_indic(self, text: str, target_lang: str) -> str:
        """Translate from English to Indic language"""
        try:
            # Ensure model is loaded
            if self.en_indic_model is None:
                logger.info("En->Indic model not loaded, loading now...")
                self._load_en_to_indic_model()
            
            # Ensure processor is initialized
            if self.ip is None:
                logger.info("Initializing IndicProcessor...")
                self.ip = IndicProcessor(inference=True)
            
            # Preprocess
            logger.info(f"Preprocessing text for translation to {target_lang}")
            batch = self.ip.preprocess_batch(
                [text],
                src_lang="eng_Latn",
                tgt_lang=target_lang
            )
            logger.info(f"Preprocessed batch: {batch}")
            
            # Tokenize
            inputs = self.en_indic_tokenizer(
                batch,
                truncation=True,
                padding="longest",
                return_tensors="pt",
                return_attention_mask=True
            ).to(self.device)
            
            # Generate translation
            with torch.no_grad():
                generated_tokens = self.en_indic_model.generate(
                    **inputs,
                    use_cache=True,
                    min_length=0,
                    max_length=256,
                    num_beams=5,
                    num_return_sequences=1
                )
            
            # Decode
            generated_tokens = self.en_indic_tokenizer.batch_decode(
                generated_tokens.detach().cpu().tolist(),
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            
            logger.info(f"Raw decoded output: {generated_tokens}")
            
            # Postprocess
            translations = self.ip.postprocess_batch(
                generated_tokens,
                lang=target_lang
            )
            
            logger.info(f"Postprocessed translation: {translations}")
            return translations[0] if translations else text
            
        except Exception as e:
            logger.error(f"En->Indic translation error: {e}", exc_info=True)
            return text
    
    def _translate_indic_to_en(self, text: str, source_lang: str) -> str:
        """Translate from Indic language to English"""
        try:
            # Ensure model is loaded
            if self.indic_en_model is None:
                logger.info("Indic->En model not loaded, loading now...")
                self._load_indic_to_en_model()
            
            # Ensure processor is initialized
            if self.ip is None:
                logger.info("Initializing IndicProcessor...")
                self.ip = IndicProcessor(inference=True)
            
            # Preprocess
            logger.info(f"Preprocessing Indic text from {source_lang}")
            batch = self.ip.preprocess_batch(
                [text],
                src_lang=source_lang,
                tgt_lang="eng_Latn"
            )
            logger.info(f"Preprocessed batch: {batch}")
            
            # Tokenize
            inputs = self.indic_en_tokenizer(
                batch,
                truncation=True,
                padding="longest",
                return_tensors="pt",
                return_attention_mask=True
            ).to(self.device)
            
            # Generate translation
            with torch.no_grad():
                generated_tokens = self.indic_en_model.generate(
                    **inputs,
                    use_cache=True,
                    min_length=0,
                    max_length=256,
                    num_beams=5,
                    num_return_sequences=1
                )
            
            # Decode
            generated_tokens = self.indic_en_tokenizer.batch_decode(
                generated_tokens.detach().cpu().tolist(),
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            
            logger.info(f"Raw decoded output: {generated_tokens}")
            
            # Postprocess
            translations = self.ip.postprocess_batch(
                generated_tokens,
                lang="eng_Latn"
            )
            
            logger.info(f"Postprocessed translation: {translations}")
            return translations[0] if translations else text
            
        except Exception as e:
            logger.error(f"Indic->En translation error: {e}", exc_info=True)
            return text
    
    async def detect_language(self, text: str) -> str:
        """
        Detect language from text using Unicode ranges
        Returns language code (e.g., 'hi', 'ta', 'en')
        """
        if not text:
            return "en"
        
        # Count characters in different scripts
        script_counts = {
            'devanagari': 0,  # Hindi, Marathi
            'tamil': 0,
            'telugu': 0,
            'kannada': 0,
            'bengali': 0,  # Bengali, Assamese
            'gujarati': 0,
            'malayalam': 0,
            'gurmukhi': 0,  # Punjabi
            'latin': 0
        }
        
        for char in text:
            code = ord(char)
            if 0x0900 <= code <= 0x097F:
                script_counts['devanagari'] += 1
            elif 0x0B80 <= code <= 0x0BFF:
                script_counts['tamil'] += 1
            elif 0x0C00 <= code <= 0x0C7F:
                script_counts['telugu'] += 1
            elif 0x0C80 <= code <= 0x0CFF:
                script_counts['kannada'] += 1
            elif 0x0980 <= code <= 0x09FF:
                script_counts['bengali'] += 1
            elif 0x0A80 <= code <= 0x0AFF:
                script_counts['gujarati'] += 1
            elif 0x0D00 <= code <= 0x0D7F:
                script_counts['malayalam'] += 1
            elif 0x0A00 <= code <= 0x0A7F:
                script_counts['gurmukhi'] += 1
            elif (0x0041 <= code <= 0x005A) or (0x0061 <= code <= 0x007A):
                script_counts['latin'] += 1
        
        # Find dominant script
        dominant_script = max(script_counts, key=script_counts.get)
        
        # Map script to language code
        script_to_lang = {
            'devanagari': 'hi',  # Default to Hindi
            'tamil': 'ta',
            'telugu': 'te',
            'kannada': 'kn',
            'bengali': 'bn',
            'gujarati': 'gu',
            'malayalam': 'ml',
            'gurmukhi': 'pa',
            'latin': 'en'
        }
        
        detected = script_to_lang.get(dominant_script, 'en')
        logger.info(f"Detected language: {detected} (script: {dominant_script})")
        
        return detected
    
    async def batch_translate(
        self,
        texts: list[str],
        source_lang: str,
        target_lang: str
    ) -> list[str]:
        """Translate multiple texts efficiently"""
        translations = []
        for text in texts:
            translated = await self.translate(text, source_lang, target_lang)
            translations.append(translated)
        return translations
    
    def clear_cache(self):
        """Clear translation cache"""
        self.cache.clear()
        logger.info("Translation cache cleared")

# Singleton instance
translation_service = IndicTrans2Service()
