# Create app/services/indic_toolkit.py (helper)
# This is a simplified version - you may need to adjust based on actual IndicTransToolkit

class IndicProcessor:
    """Simple preprocessor/postprocessor for IndicTrans2"""
    
    def __init__(self, inference=True):
        self.inference = inference
    
    def preprocess_batch(self, sentences, src_lang, tgt_lang):
        """Preprocess sentences for translation"""
        # Add special tokens if needed
        processed = [f"{src_lang} {tgt_lang} {sent}" for sent in sentences]
        return processed
    
    def postprocess_batch(self, sentences, lang):
        """Postprocess translated sentences"""
        # Remove special tokens, clean up
        cleaned = [sent.strip() for sent in sentences]
        return cleaned
