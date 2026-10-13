"""
Script to download and cache IndicTrans2 models
Run this once before starting the server to avoid delays

NOTE: These models require Hugging Face authentication and access approval.
1. Request access at: https://huggingface.co/ai4bharat/indictrans2-en-indic-1B
2. Request access at: https://huggingface.co/ai4bharat/indictrans2-indic-en-1B
3. Add HUGGINGFACE_HUB_TOKEN to your .env file
"""

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sys
from huggingface_hub import login

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_models():
    """Download both IndicTrans2 models"""
    
    # Check authentication first
    if not settings.HUGGINGFACE_HUB_TOKEN:
        logger.error("❌ No HUGGINGFACE_HUB_TOKEN found in settings!")
        logger.error("🔑 Please add HUGGINGFACE_HUB_TOKEN to your .env file")
        logger.error("📝 And request access to the models:")
        logger.error("  - https://huggingface.co/ai4bharat/indictrans2-en-indic-1B")
        logger.error("  - https://huggingface.co/ai4bharat/indictrans2-indic-en-1B")
        return False
    
    # Authenticate with Hugging Face
    try:
        logger.info("🔑 Authenticating with Hugging Face...")
        login(token=settings.HUGGINGFACE_HUB_TOKEN)
        logger.info("✅ Hugging Face authentication successful")
    except Exception as e:
        logger.error(f"❌ Hugging Face authentication failed: {e}")
        return False
    
    models = [
        ("ai4bharat/indictrans2-en-indic-1B", "English to Indic"),
        ("ai4bharat/indictrans2-indic-en-1B", "Indic to English")
    ]
    
    success = True
    for model_name, description in models:
        logger.info(f"\n{'='*60}")
        logger.info(f"Downloading {description} model: {model_name}")
        logger.info(f"{'='*60}\n")
        
        try:
            # Download tokenizer
            logger.info("Downloading tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            logger.info("✅ Tokenizer downloaded")
            
            # Download model
            logger.info("Downloading model (this may take a few minutes)...")
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            logger.info("✅ Model downloaded")
            
            logger.info(f"✅ {description} model ready!\n")
        except Exception as e:
            logger.error(f"❌ Error downloading {description} model: {e}")
            if "gated repo" in str(e):
                logger.error(f"🔒 This is a gated repository.")
                logger.error(f"📝 Please request access at: https://huggingface.co/{model_name}")
                logger.error(f"🔑 Then add HUGGINGFACE_HUB_TOKEN to your .env file")
            success = False
    
    return success

if __name__ == "__main__":
    logger.info("Starting IndicTrans2 model download...")
    logger.info("Note: Models are ~2GB each, this will take some time\n")
    
    success = download_models()
    
    if success:
        logger.info("\n" + "="*60)
        logger.info("🎉 All models downloaded successfully!")
        logger.info("You can now start the server with: python -m app.main")
        logger.info("="*60 + "\n")
    else:
        logger.error("\n" + "="*60)
        logger.error("❌ Model download failed. Please check the error messages above.")
        logger.error("="*60 + "\n")
