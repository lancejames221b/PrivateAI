#!/usr/bin/env python3
"""
Transformer Debugging Script
This script diagnoses issues with Hugging Face transformers and attempts to solve them.
It runs various tests to isolate issues with downloading models, proxy settings, and compatibility.
"""

import os
import sys
import logging
import tempfile
import platform
import subprocess
import requests
from pathlib import Path
import traceback
import importlib
import ssl
import socket
import time
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("transformer_debug.log")
    ]
)
logger = logging.getLogger("transformer-debug")

def check_environment():
    """Check the Python environment and packages"""
    logger.info("=== Environment Check ===")
    env_info = {
        "platform": platform.platform(),
        "python_version": sys.version,
        "executable": sys.executable,
        "cwd": os.getcwd(),
        "pip_path": subprocess.getoutput("which pip"),
    }
    
    for key, value in env_info.items():
        logger.info(f"{key}: {value}")
    
    # Check for virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        logger.info("Running in a virtual environment")
    else:
        logger.warning("Not running in a virtual environment")
    
    return env_info

def check_proxy_settings():
    """Check proxy settings in the environment"""
    logger.info("=== Proxy Settings Check ===")
    proxy_vars = ["http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy", "ALL_PROXY", "no_proxy", "NO_PROXY"]
    found_proxies = False
    
    for var in proxy_vars:
        if var in os.environ:
            logger.info(f"{var}={os.environ[var]}")
            found_proxies = True
    
    if not found_proxies:
        logger.info("No proxy environment variables detected")
    
    return found_proxies

def check_network_connectivity():
    """Check basic network connectivity"""
    logger.info("=== Network Connectivity Check ===")
    test_urls = [
        "https://huggingface.co",
        "https://cdn-lfs.huggingface.co",
        "https://s3.amazonaws.com",
        "https://www.google.com"  # Control test
    ]
    
    results = {}
    for url in test_urls:
        logger.info(f"Testing connection to {url}...")
        try:
            # First try a basic socket connection to check if host is reachable
            hostname = url.split("//")[1].split("/")[0]
            socket.create_connection((hostname, 443), timeout=10)
            logger.info(f"Socket connection to {hostname}:443 successful")
            
            # Now try a full HTTPS request
            start_time = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start_time
            
            results[url] = {
                "status_code": response.status_code,
                "response_time": f"{elapsed:.2f}s",
                "success": response.status_code == 200
            }
            
            logger.info(f"Connection to {url} successful (status: {response.status_code}, time: {elapsed:.2f}s)")
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL Error connecting to {url}: {e}")
            results[url] = {"error": "SSL Error", "details": str(e)}
        except socket.timeout:
            logger.error(f"Timeout connecting to {url}")
            results[url] = {"error": "Timeout"}
        except socket.gaierror as e:
            logger.error(f"DNS resolution error for {url}: {e}")
            results[url] = {"error": "DNS Error", "details": str(e)}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            results[url] = {"error": "Connection Error", "details": str(e)}
        except Exception as e:
            logger.error(f"Error testing {url}: {e}")
            results[url] = {"error": "Other Error", "details": str(e)}
    
    return results

def check_ssl_certificates():
    """Check SSL certificate settings"""
    logger.info("=== SSL Certificate Check ===")
    
    # Get SSL version
    logger.info(f"SSL Version: {ssl.OPENSSL_VERSION}")
    
    # Check if custom certificates are involved
    cert_vars = ["SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"]
    custom_certs = False
    
    for var in cert_vars:
        if var in os.environ:
            logger.info(f"{var}={os.environ[var]}")
            custom_certs = True
    
    if not custom_certs:
        logger.info("No custom certificate paths detected in environment")
    
    # Test SSL connection to Hugging Face
    try:
        context = ssl.create_default_context()
        with socket.create_connection(("huggingface.co", 443)) as sock:
            with context.wrap_socket(sock, server_hostname="huggingface.co") as ssock:
                cert = ssock.getpeercert()
                logger.info(f"SSL connection to huggingface.co successful")
                logger.info(f"Certificate subject: {cert['subject']}")
                logger.info(f"Certificate issuer: {cert['issuer']}")
    except Exception as e:
        logger.error(f"SSL connection test failed: {e}")
    
    return custom_certs

def check_installed_packages():
    """Check installed packages and their versions"""
    logger.info("=== Installed Packages Check ===")
    packages = [
        "torch", "numpy", "transformers", "requests",
        "huggingface_hub", "tokenizers", "presidio-analyzer"
    ]
    
    results = {}
    for package in packages:
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "Unknown")
            results[package] = version
            logger.info(f"{package}: {version}")
        except ImportError:
            logger.warning(f"{package} is not installed")
            results[package] = None
    
    # Check interdependencies
    try:
        import numpy
        import torch
        logger.info(f"NumPy is using: {numpy.__config__.show()}")
    except:
        logger.warning("Could not check NumPy configuration")
    
    return results

def test_transformers_import():
    """Test importing transformers components"""
    logger.info("=== Transformers Import Test ===")
    components = [
        "pipeline", "AutoTokenizer", "AutoModelForTokenClassification",
        "AutoModelForSequenceClassification", "AutoModelForQuestionAnswering"
    ]
    
    results = {}
    for component in components:
        try:
            import_cmd = f"from transformers import {component}"
            exec(import_cmd)
            results[component] = "Success"
            logger.info(f"Successfully imported {component}")
        except Exception as e:
            error_msg = str(e)
            results[component] = f"Error: {error_msg}"
            logger.error(f"Failed to import {component}: {error_msg}")
    
    return results

def test_model_download(model_name="distilbert-base-uncased", no_proxy=True):
    """Test downloading a specific model"""
    logger.info(f"=== Model Download Test: {model_name} ===")
    
    # Create a clean environment without proxy settings if requested
    env = os.environ.copy()
    if no_proxy:
        proxy_vars = ["http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]
        for var in proxy_vars:
            if var in env:
                del env[var]
        logger.info("Proxy settings removed from environment")
    
    # Create a temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            logger.info(f"Using temporary directory: {temp_dir}")
            
            # Try downloading with transformers directly
            from transformers import AutoTokenizer
            
            start_time = time.time()
            logger.info(f"Attempting to download tokenizer for {model_name}...")
            tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=temp_dir)
            elapsed = time.time() - start_time
            
            logger.info(f"Successfully downloaded tokenizer in {elapsed:.2f}s")
            logger.info(f"Tokenizer type: {type(tokenizer).__name__}")
            
            # Try loading model to verify
            from transformers import AutoModel
            
            start_time = time.time()
            logger.info(f"Attempting to download model for {model_name}...")
            model = AutoModel.from_pretrained(model_name, cache_dir=temp_dir)
            elapsed = time.time() - start_time
            
            logger.info(f"Successfully downloaded model in {elapsed:.2f}s")
            logger.info(f"Model type: {type(model).__name__}")
            
            return {
                "success": True,
                "model_name": model_name,
                "tokenizer_type": type(tokenizer).__name__,
                "model_type": type(model).__name__,
                "download_time": elapsed
            }
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Failed to download {model_name}: {e}")
            logger.error(f"Traceback: {error_traceback}")
            
            return {
                "success": False,
                "model_name": model_name,
                "error": str(e),
                "traceback": error_traceback
            }

def test_simple_models():
    """Test downloading various small models to find one that works"""
    logger.info("=== Testing Simple Models ===")
    models = [
        "distilbert-base-uncased",  # Small general purpose model
        "bert-base-uncased",        # Popular model
        "gpt2",                     # Small GPT model
        "prajjwal1/bert-tiny",      # Very small BERT
        "sshleifer/tiny-distilbert-base-cased"  # Tiny model
    ]
    
    results = {}
    for model in models:
        logger.info(f"Testing model: {model}")
        result = test_model_download(model)
        results[model] = result
        
        if result["success"]:
            logger.info(f"Model {model} downloaded successfully!")
        else:
            logger.error(f"Model {model} failed to download")
    
    return results

def test_ner_models():
    """Test downloading various NER models to find one that works"""
    logger.info("=== Testing NER Models ===")
    models = [
        "dslim/bert-base-NER",           # Standard NER model
        "dbmdz/bert-large-cased-finetuned-conll03-english",  # Another NER model
        "elastic/distilbert-base-uncased-finetuned-conll03-english",  # Elastic NER
        "flair/ner-english-ontonotes-large"  # Flair NER
    ]
    
    results = {}
    for model in models:
        logger.info(f"Testing NER model: {model}")
        result = test_model_download(model)
        results[model] = result
        
        if result["success"]:
            logger.info(f"NER Model {model} downloaded successfully!")
        else:
            logger.error(f"NER Model {model} failed to download")
    
    return results

def test_transformer_pipeline(model_name=None):
    """Test the transformer pipeline for token classification"""
    logger.info("=== Testing Transformer Pipeline ===")
    
    try:
        from transformers import pipeline
        
        if model_name:
            logger.info(f"Testing pipeline with model: {model_name}")
            nlp = pipeline("ner", model=model_name, aggregation_strategy="simple")
        else:
            logger.info("Testing pipeline with default model")
            nlp = pipeline("ner", aggregation_strategy="simple")
        
        # Test with a simple example
        text = "John Smith works at Microsoft in Seattle."
        
        logger.info(f"Running NER pipeline on: '{text}'")
        results = nlp(text)
        
        logger.info(f"Pipeline results: {results}")
        return {
            "success": True,
            "model": model_name or "default",
            "results": results
        }
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"Pipeline test failed: {e}")
        logger.error(f"Traceback: {error_traceback}")
        
        return {
            "success": False,
            "model": model_name or "default",
            "error": str(e),
            "traceback": error_traceback
        }

def test_offline_model():
    """Test the offline model"""
    logger.info("=== Testing Offline Model ===")
    
    try:
        # Import offline model
        offline_model_path = Path("models/dist/offline_model.py")
        
        if not offline_model_path.exists():
            logger.error(f"Offline model not found at {offline_model_path}")
            return {"success": False, "error": "Offline model file not found"}
        
        # Add the models/dist directory to path
        sys.path.append(str(offline_model_path.parent))
        
        # Try importing modules from the offline model
        logger.info("Importing offline model...")
        import offline_model
        from offline_model import OfflineModel, pipeline
        
        # Create model and test
        model = OfflineModel()
        
        # Test with a simple example
        text = "John Smith works at Microsoft in Seattle."
        
        logger.info(f"Running offline model on: '{text}'")
        results = model(text)
        
        # Test with pipeline
        nlp = pipeline("ner", model=model)
        pipeline_results = nlp(text)
        
        logger.info(f"Offline model results: {results}")
        logger.info(f"Offline pipeline results: {pipeline_results}")
        
        return {
            "success": True,
            "direct_results": results,
            "pipeline_results": pipeline_results
        }
    except Exception as e:
        error_traceback = traceback.format_exc()
        logger.error(f"Offline model test failed: {e}")
        logger.error(f"Traceback: {error_traceback}")
        
        return {
            "success": False,
            "error": str(e),
            "traceback": error_traceback
        }

def fix_transformers_issues():
    """Attempt to fix common issues with transformers"""
    logger.info("=== Fixing Transformers Issues ===")
    fixes_applied = []
    
    # 1. Try to create a models directory if it doesn't exist
    models_dir = Path("models")
    if not models_dir.exists():
        models_dir.mkdir(parents=True)
        logger.info("Created models directory")
        fixes_applied.append("Created models directory")
    
    # 2. Check and fix SSL certificate issues
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Test connection with modified SSL context
        with socket.create_connection(("huggingface.co", 443)) as sock:
            with ssl_context.wrap_socket(sock, server_hostname="huggingface.co") as ssock:
                logger.info("SSL connection with verification disabled successful")
                fixes_applied.append("Tested SSL without verification")
    except Exception as e:
        logger.error(f"SSL test failed: {e}")
    
    # 3. Try installing a known compatible version of transformers and dependencies
    try:
        logger.info("Checking if we need to fix package versions...")
        import numpy
        import torch
        import transformers
        
        numpy_version = numpy.__version__
        torch_version = torch.__version__
        transformers_version = transformers.__version__
        
        logger.info(f"Current versions - NumPy: {numpy_version}, PyTorch: {torch_version}, Transformers: {transformers_version}")
        
        # Only attempt to fix if versions seem incompatible
        if "4.30.2" in transformers_version and "1.13" in torch_version:
            logger.info("Versions appear compatible, skipping package fixes")
        else:
            logger.warning("Versions may be incompatible, consider reinstalling with compatible versions")
            fixes_applied.append("Identified potential version incompatibility")
    except Exception as e:
        logger.error(f"Version check failed: {e}")
    
    return fixes_applied

def create_test_script():
    """Create a simple test script for using transformers"""
    logger.info("=== Creating Test Script ===")
    
    test_script_path = Path("test_transformers.py")
    
    script_content = '''#!/usr/bin/env python3
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
'''
    
    with open(test_script_path, "w") as f:
        f.write(script_content)
    
    logger.info(f"Test script created at {test_script_path}")
    logger.info("Run it with: python test_transformers.py")
    
    # Make it executable
    test_script_path.chmod(test_script_path.stat().st_mode | 0o755)
    
    return str(test_script_path)

def main():
    """Run all tests and diagnostics"""
    logger.info("Starting transformer diagnostics")
    
    results = {}
    
    # Run basic environment checks
    results["environment"] = check_environment()
    results["proxy_settings"] = check_proxy_settings()
    results["connectivity"] = check_network_connectivity()
    results["ssl_certificates"] = check_ssl_certificates()
    results["installed_packages"] = check_installed_packages()
    results["transformers_import"] = test_transformers_import()
    
    # Test downloading models
    logger.info("Testing model downloads...")
    results["simple_models"] = test_simple_models()
    results["ner_models"] = test_ner_models()
    
    # Find a working model
    working_model = None
    for model, result in results["simple_models"].items():
        if result.get("success", False):
            working_model = model
            break
    
    if working_model:
        logger.info(f"Found working model: {working_model}")
        results["pipeline_test"] = test_transformer_pipeline(working_model)
    else:
        logger.warning("No working model found, testing with default pipeline")
        results["pipeline_test"] = test_transformer_pipeline()
    
    # Test offline model fallback
    results["offline_model"] = test_offline_model()
    
    # Apply fixes
    results["fixes"] = fix_transformers_issues()
    
    # Create test script
    results["test_script"] = create_test_script()
    
    # Save all results to JSON file
    with open("transformer_diagnostics.json", "w") as f:
        # Convert non-serializable types to strings
        def json_serializer(obj):
            if isinstance(obj, Exception):
                return str(obj)
            raise TypeError(f"Type {type(obj)} not serializable")
        
        json.dump(results, f, indent=2, default=json_serializer)
    
    logger.info("Diagnostics complete. Results saved to transformer_diagnostics.json")
    logger.info(f"Run the test script: python {results['test_script']}")
    
    return results

if __name__ == "__main__":
    main() 