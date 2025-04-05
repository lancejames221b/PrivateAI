# Setting Up Transformers for PII Detection

This guide explains how to set up and use Hugging Face's Transformers library for enhanced PII detection in the Private AI Proxy.

## Overview

The Private AI Proxy includes advanced PII detection capabilities using transformer-based models from Hugging Face. These models provide more accurate entity recognition than traditional regex patterns, especially for complex entities like names, organizations, and locations.

## Prerequisites

Before using transformer-based PII detection, ensure you have:

1. Python 3.9+ installed
2. A compatible environment with the following packages:
   - transformers==4.30.2
   - torch==1.13.1
   - numpy==1.23.5
   - accelerate==0.20.3

These specific versions are known to work well together. Using different versions may lead to compatibility issues.

## Installation

If you haven't already installed the required packages, you can add them to your environment:

```bash
pip install transformers==4.30.2 torch==1.13.1 numpy==1.23.5 accelerate==0.20.3
```

## Setup Options

The system supports three modes of operation, with automatic fallback between them:

1. **Online Transformer Models**: Downloads models from Hugging Face on demand
2. **Offline Model**: Uses a built-in model that doesn't require downloading
3. **Regex Patterns**: Falls back to regex patterns when models aren't available

## Downloading Models Before Starting the Proxy

To avoid having the proxy intercept model downloads (which can cause SSL issues), you should download models before starting the proxy:

```bash
# Stop the proxy if it's running
python scripts/proxy_service.py --stop

# Clear any proxy environment variables
export http_proxy=''
export https_proxy=''
export HTTP_PROXY=''
export HTTPS_PROXY=''

# Run the model download script
python scripts/download_transformers_models.py
```

The script will download the following models to the `models/` directory:
- `dslim/bert-base-NER` (Default NER model)
- Other models as configured

## Troubleshooting Common Issues

### Running the Diagnostic Script

If you're experiencing issues with transformer models, run the comprehensive diagnostic script:

```bash
python scripts/debug_transformers.py
```

This script performs a series of tests including:
- Environment configuration checks
- Package version compatibility checks
- Network connectivity tests to Hugging Face servers
- SSL certificate validation
- Model download tests with multiple models
- Transformer pipeline tests
- Offline model validation

The results are saved to `transformer_diagnostics.json` and logged to `transformer_debug.log`.

### Accelerate Version Compatibility

If you see this error:
```
TypeError: named_parameters() got an unexpected keyword argument 'remove_duplicate'
```

The solution is to downgrade the accelerate library:
```bash
pip install accelerate==0.20.3
```

### NumPy Compatibility Issues

If you encounter NumPy compatibility warnings or errors, ensure you're using a compatible version:
```bash
pip install numpy==1.23.5
```

### SSL/Download Errors

If models fail to download due to SSL errors, it's likely because:
1. The proxy is intercepting the connection
2. Your SSL certificates need updating
3. Network connectivity issues

Try:
- Disabling proxy settings
- Running the download script without the proxy active
- Checking your connection to huggingface.co

### GPU/CUDA Issues

If you see errors related to CUDA or GPU:
1. Ensure your CUDA drivers are compatible with your PyTorch version
2. Try forcing CPU mode by setting environment variables:
   ```bash
   export CUDA_VISIBLE_DEVICES=-1
   ```

### Memory Issues

If you're experiencing out-of-memory errors:
1. Try a smaller model like `prajjwal1/bert-tiny`
2. Ensure you have at least 4GB of available RAM
3. Close other memory-intensive applications

## Using Offline Mode

If you can't download models, the system will automatically fall back to the offline model which uses sophisticated regex patterns. This works without internet access and doesn't require downloading any models.

The offline model is located at `models/dist/offline_model.py` and provides good performance without the need for external downloads.

## Testing Your Setup

You can test if transformers are working correctly by running:

```bash
python scripts/test_transformers.py
```

This will test:
1. Loading the offline model
2. Downloading and using an online model
3. Running the NER pipeline with a standard model

You can also run a quick functionality test directly:

```python
from transformers_recognizer import TransformersRecognizer
r = TransformersRecognizer()
print('Model loaded:', r.model is not None)
print('Using offline model:', r.using_offline_model)
print('Using regex fallback:', r.using_regex_fallback)
```

## Advanced Configuration

You can modify the `transformers_recognizer.py` file to change:
- Default models used
- Confidence thresholds
- Entity mapping
- Fallback behavior

### Available Environment Variables

- `TRANSFORMERS_MODEL`: Set a custom transformer model (default is `dslim/bert-base-NER`)
- `TRANSFORMERS_FALLBACK_MODEL`: Specify a fallback model to try if the main one fails
- `TRANSFORMERS_CONFIDENCE_THRESHOLD`: Set the minimum confidence threshold (0.0-1.0)
- `TRANSFORMERS_OFFLINE_ONLY`: Set to `1` to only use the offline model
- `TRANSFORMERS_CACHE_DIR`: Set custom cache directory for downloaded models

## Performance Considerations

- Transformer models provide better accuracy but require more memory and CPU
- First-time model loading can take a few seconds
- Subsequent inference is much faster after the model is loaded
- The offline model is faster but less accurate for complex entities
- Regex patterns are fastest but least accurate

## Version Compatibility Matrix

| transformers | torch | numpy | accelerate | Status |
|--------------|-------|-------|------------|--------|
| 4.30.2       | 1.13.1| 1.23.5| 0.20.3     | ✓ Working |
| 4.30.2       | 1.13.1| 1.23.5| 0.21.0+    | ✗ Named parameters error |
| 4.30.2       | 1.13.1| 2.0.0+ | 0.20.3    | ✗ NumPy compatibility issues |
| 4.31.0+      | 1.13.1| 1.23.5| 0.20.3     | ⚠ Not fully tested |

## Further Help

If you continue to encounter issues, check:
- The latest release notes for the transformers library
- Your Python and package versions
- Network configuration for downloading models
- Memory constraints if models fail to load
- The diagnostic output from `debug_transformers.py` 