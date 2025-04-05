#!/usr/bin/env python3
# Test script for Hugging Face transformers
import os
import sys
import logging
from pathlib import Path

# Clear proxy settings
proxy_vars = ["http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("transformer-test")

def test_offline_model():
    """Test the offline fallback model"""
    logger.info("Testing offline model...")
    
    try:
        # Import from local path
        offline_model_path = Path("models/dist")
        if offline_model_path.exists():
            sys.path.append(str(offline_model_path))
            
            from offline_model import OfflineModel, pipeline
            
            # Create model
            model = OfflineModel()
            
            # Test with sample text
            text = "John Smith works for Acme Corp in New York. His email is john@acme.com."
            results = model(text)
            
            logger.info(f"Found {len(results)} entities in offline mode:")
            for entity in results:
                logger.info(f"  {entity['entity_group']}: {entity['word']} (score: {entity['score']:.2f})")
                
            return True
    except Exception as e:
        logger.error(f"Offline model test failed: {e}")
    
    return False

def test_online_model(model_name="distilbert-base-uncased"):
    """Test downloading and using a model from Hugging Face"""
    logger.info(f"Testing online model: {model_name}")
    
    try:
        from transformers import AutoTokenizer, AutoModel
        
        # Try loading tokenizer
        logger.info(f"Loading tokenizer for {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Try loading model
        logger.info(f"Loading model for {model_name}...")
        model = AutoModel.from_pretrained(model_name)
        
        logger.info(f"Successfully loaded {model_name}")
        
        # Test tokenizing some text
        text = "Testing transformer models with Hugging Face"
        logger.info(f"Tokenizing: '{text}'")
        tokens = tokenizer(text, return_tensors="pt")
        logger.info(f"Tokenization successful")
        
        return True
    except Exception as e:
        logger.error(f"Online model test failed: {e}")
    
    return False

def test_ner_pipeline(model_name="dslim/bert-base-NER"):
    """Test NER pipeline with a specific model"""
    logger.info(f"Testing NER pipeline with {model_name}")
    
    try:
        from transformers import pipeline
        
        # Try creating NER pipeline
        logger.info("Creating NER pipeline...")
        nlp = pipeline("ner", model=model_name, aggregation_strategy="simple")
        
        # Test with sample text
        text = "John Smith works for Microsoft in Seattle and his colleague is Bill Gates."
        logger.info(f"Running NER on: '{text}'")
        
        results = nlp(text)
        
        logger.info(f"Found {len(results)} entities:")
        for entity in results:
            logger.info(f"  {entity['entity_group']}: {entity['word']} (score: {entity['score']:.2f})")
            
        return True
    except Exception as e:
        logger.error(f"NER pipeline test failed: {e}")
    
    return False

def main():
    """Run all tests"""
    logger.info("Starting transformer tests")
    
    # Test if we can use offline model
    offline_successful = test_offline_model()
    logger.info(f"Offline model test: {'✓ Passed' if offline_successful else '× Failed'}")
    
    # Test if we can download and use an online model
    online_successful = test_online_model("prajjwal1/bert-tiny")  # Try a tiny model first
    logger.info(f"Online model test: {'✓ Passed' if online_successful else '× Failed'}")
    
    # Test if we can use a NER pipeline
    if online_successful:
        ner_successful = test_ner_pipeline("dslim/bert-base-NER")
        logger.info(f"NER pipeline test: {'✓ Passed' if ner_successful else '× Failed'}")
    else:
        logger.warning("Skipping NER test because online model test failed")
    
    logger.info("Tests completed")

if __name__ == "__main__":
    main()
