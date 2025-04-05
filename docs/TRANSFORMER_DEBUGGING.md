# Debugging Transformer Models in Private AI

This guide provides detailed troubleshooting steps for transformer model issues in the Private AI proxy.

## Using the Debugging Script

The `debug_transformers.py` script automates many diagnostic checks to identify transformer model issues:

```bash
python scripts/debug_transformers.py
```

## Common Issues and Solutions

### 1. Import Errors

#### Symptoms:
- Error messages like "No module named 'transformers'"
- System falling back to regex patterns

#### Solutions:
- Verify the required packages are installed:
  ```bash
  pip install transformers==4.30.2 torch==1.13.1 numpy==1.23.5 accelerate==0.20.3
  ```
- Check for conflicts between dependencies: `pip check`
- Ensure your Python environment is activated correctly

### 2. Model Download Issues

#### Symptoms:
- Warnings about model downloads failing
- Errors connecting to huggingface.co

#### Solutions:
- Clear proxy environment variables before downloading:
  ```bash
  export http_proxy='' https_proxy='' HTTP_PROXY='' HTTPS_PROXY=''
  ```
- Check network connectivity to huggingface.co:
  ```bash
  curl -v https://huggingface.co
  ```
- Verify your SSL certificates are working:
  ```bash
  python -c "import ssl; print(ssl.OPENSSL_VERSION)"
  ```

### 3. CUDA/GPU Errors

#### Symptoms:
- CUDA out of memory errors
- CUDA initialization failed

#### Solutions:
- Force CPU-only mode:
  ```bash
  export CUDA_VISIBLE_DEVICES=-1
  ```
- Update CUDA drivers if using GPU acceleration
- Try a smaller model like `prajjwal1/bert-tiny`

### 4. Compatibility Errors

#### Symptoms:
- `TypeError: named_parameters() got an unexpected keyword argument 'remove_duplicate'`
- Numpy binary incompatibility warnings

#### Solutions:
- Use the specific dependency versions known to work together:
  ```bash
  pip install accelerate==0.20.3 numpy==1.23.5
  ```
- Check Python version (3.9+ recommended)
- Check transformers version is correct: `pip show transformers`

### 5. Memory Issues

#### Symptoms:
- Out of memory errors
- Model loading fails with resource errors

#### Solutions:
- Free system memory by closing other applications
- Use a smaller model (try `prajjwal1/bert-tiny`)
- Increase swap space temporarily if needed

## Diagnostics Decision Tree

1. **Can the system import transformers?**
   - No → Check package installation
   - Yes → Continue

2. **Can the system download models from Hugging Face?**
   - No → Check network, proxy settings, and SSL certificates
   - Yes → Continue

3. **Does the model load correctly?**
   - No → Check memory usage and compatibility
   - Yes → Continue

4. **Does the model produce entity predictions?**
   - No → Check model type/format and input data
   - Yes → Success!

## Manual Testing

Test basic model functionality directly in Python:

```python
# Test model downloads
from transformers import AutoTokenizer, AutoModelForTokenClassification
tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")
print("Model loaded successfully!")

# Test our recognizer directly
from transformers_recognizer import TransformersRecognizer
recognizer = TransformersRecognizer()
print(f"Model loaded: {recognizer.model is not None}")
print(f"Using offline: {recognizer.using_offline_model}")
print(f"Using regex: {recognizer.using_regex_fallback}")

# Try prediction on sample text
text = "John Smith works at Microsoft in Seattle."
entities = ["PERSON", "ORGANIZATION", "LOCATION"]
results = recognizer.analyze(text, entities)
print(f"Found {len(results)} entities")
for result in results:
    print(f"{result.entity_type}: {text[result.start:result.end]} (score: {result.score:.2f})")
```

## Environment Variables

You can modify transformer behavior with these environment variables:

- `TRANSFORMERS_OFFLINE=1` - Force offline mode (no downloads)
- `TRANSFORMERS_VERBOSITY=info` - Set logging level (info, warning, error, critical)
- `CUDA_VISIBLE_DEVICES=-1` - Force CPU-only mode
- `TRANSFORMERS_CACHE=/path/to/cache` - Set custom cache location
- `TOKENIZERS_PARALLELISM=false` - Disable parallel tokenization if causing issues

## Generating Configuration Manifest

Generate a manifest of your environment for troubleshooting:

```bash
python -c "import torch; import transformers; import numpy; import accelerate; print(f'Python: {sys.version}\\nPyTorch: {torch.__version__}\\nTransformers: {transformers.__version__}\\nNumPy: {numpy.__version__}\\nAccelerate: {accelerate.__version__ if hasattr(accelerate, \"__version__\") else \"unknown\"}')" > transformer_config.txt
```

## Getting Support

If you've tried all the steps above and still encountering issues:

1. Run the diagnostic script
2. Gather the `transformer_debug.log` and `transformer_diagnostics.json` files
3. Generate the configuration manifest
4. Open an issue on GitHub with these files attached 