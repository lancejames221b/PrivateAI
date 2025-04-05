#!/usr/bin/env python3
"""
Download Transformer Models Script
Downloads transformer models for offline use before starting the proxy
"""

import os
import sys
import logging
from pathlib import Path
import json
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("model-downloader")

# Default models to download
DEFAULT_MODELS = [
    "dslim/bert-base-NER",         # Primary NER model
    "prajjwal1/bert-tiny",         # Small fallback model
]

def clear_proxy_settings():
    """Clear proxy environment variables to ensure direct connection"""
    proxy_vars = ["http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]
    cleared = False
    
    for var in proxy_vars:
        if var in os.environ:
            logger.info(f"Clearing {var} environment variable")
            os.environ[var] = ""
            cleared = True
            
    if cleared:
        logger.info("Cleared proxy environment variables")
    else:
        logger.info("No proxy environment variables found")
        
    return cleared

def download_model(model_name, output_dir=None, force=False):
    """
    Download a model from Hugging Face
    
    Args:
        model_name: Name of the model to download
        output_dir: Directory to save the model (default: models/<model_short_name>)
        force: Force re-download even if model exists
        
    Returns:
        Path to the downloaded model or None if download failed
    """
    try:
        from transformers import AutoTokenizer, AutoModelForTokenClassification
        
        # Extract model short name for local path
        short_name = model_name.split("/")[-1]
        
        # Determine output directory
        if output_dir is None:
            output_dir = Path("models") / short_name
        else:
            output_dir = Path(output_dir) / short_name
            
        # Create models directory if it doesn't exist
        output_dir.parent.mkdir(exist_ok=True, parents=True)
        
        # Check if model already exists
        if output_dir.exists() and not force:
            config_path = output_dir / "config.json"
            if config_path.exists():
                logger.info(f"Model {model_name} already exists at {output_dir}")
                return output_dir
                
        # Download the model and tokenizer
        logger.info(f"Downloading {model_name} to {output_dir}...")
        
        # Download tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        tokenizer.save_pretrained(str(output_dir))
        logger.info(f"Tokenizer for {model_name} downloaded successfully")
        
        # Download model
        model = AutoModelForTokenClassification.from_pretrained(model_name)
        model.save_pretrained(str(output_dir))
        logger.info(f"Model {model_name} downloaded successfully")
        
        # Create a manifest file with model info
        manifest_dir = Path("models") / "dist"
        manifest_dir.mkdir(exist_ok=True, parents=True)
        
        manifest_path = manifest_dir / "model_info.json"
        
        # Read existing manifest or create new one
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
            except json.JSONDecodeError:
                manifest = {"models": {}}
        else:
            manifest = {"models": {}}
            
        # Add model to manifest
        manifest["models"][model_name] = {
            "path": str(output_dir),
            "type": "token-classification",
            "short_name": short_name,
            "downloaded": True
        }
        
        # Write manifest
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        logger.info(f"Updated model manifest at {manifest_path}")
        
        return output_dir
        
    except ImportError as e:
        logger.error(f"Required libraries not installed: {e}")
        logger.error("Please install transformers: pip install transformers torch")
        return None
        
    except Exception as e:
        logger.error(f"Error downloading model {model_name}: {e}")
        return None

def test_model(model_path):
    """
    Test if a downloaded model works correctly
    
    Args:
        model_path: Path to the downloaded model
        
    Returns:
        True if model works, False otherwise
    """
    try:
        from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
        
        logger.info(f"Testing model at {model_path}...")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        model = AutoModelForTokenClassification.from_pretrained(str(model_path))
        
        # Create pipeline
        nlp = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")
        
        # Test with sample text
        text = "John Smith works at Microsoft in Seattle."
        results = nlp(text)
        
        if results:
            logger.info(f"Model test successful! Found {len(results)} entities:")
            for result in results[:3]:  # Show first 3 results
                logger.info(f"  {result['entity_group']}: {result['word']} (score: {result['score']:.2f})")
            return True
        else:
            logger.warning(f"Model loaded but produced no results for test input")
            return False
            
    except Exception as e:
        logger.error(f"Error testing model: {e}")
        return False

def main():
    """Main function to download models"""
    parser = argparse.ArgumentParser(description="Download transformer models for offline use")
    parser.add_argument("--models", nargs="+", help="Models to download (space-separated)")
    parser.add_argument("--output-dir", help="Output directory for models")
    parser.add_argument("--force", action="store_true", help="Force re-download even if models exist")
    parser.add_argument("--test", action="store_true", help="Test models after downloading")
    
    args = parser.parse_args()
    
    # Clear proxy settings
    clear_proxy_settings()
    
    # Determine which models to download
    models_to_download = args.models if args.models else DEFAULT_MODELS
    
    logger.info(f"Will download {len(models_to_download)} models: {', '.join(models_to_download)}")
    
    # Download each model
    downloaded_paths = []
    for model_name in models_to_download:
        model_path = download_model(model_name, args.output_dir, args.force)
        if model_path:
            downloaded_paths.append((model_name, model_path))
    
    # Test models if requested
    if args.test and downloaded_paths:
        logger.info("Testing downloaded models...")
        for model_name, model_path in downloaded_paths:
            logger.info(f"Testing {model_name}...")
            success = test_model(model_path)
            if success:
                logger.info(f"✓ Model {model_name} works correctly")
            else:
                logger.warning(f"✗ Model {model_name} test failed")
    
    # Summary
    if downloaded_paths:
        logger.info(f"Successfully downloaded {len(downloaded_paths)} models:")
        for model_name, model_path in downloaded_paths:
            logger.info(f"  {model_name} -> {model_path}")
    else:
        logger.warning("No models were successfully downloaded")
    
    logger.info("Done!")

if __name__ == "__main__":
    main() 