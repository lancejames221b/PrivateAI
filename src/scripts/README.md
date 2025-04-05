# Private AI Proxy Scripts

This directory contains utility scripts for the Private AI Proxy.

## Transformer Model Scripts

### `download_transformers_models.py`

Downloads and prepares transformer models for offline use.

```bash
# Basic usage (downloads default models)
python scripts/download_transformers_models.py

# Download specific models
python scripts/download_transformers_models.py --models dslim/bert-base-NER prajjwal1/bert-tiny

# Force re-download existing models
python scripts/download_transformers_models.py --force

# Test models after downloading
python scripts/download_transformers_models.py --test
```

This script:
- Downloads the specified transformer models from Hugging Face
- Saves them to the `models/` directory
- Creates a manifest file at `models/dist/model_info.json`
- Optionally tests the models to ensure they work

### `debug_transformers.py`

Diagnoses and troubleshoots issues with transformer models.

```bash
python scripts/debug_transformers.py
```

This script runs a comprehensive set of diagnostic tests including:
- Environment configuration checks
- Package compatibility verification
- Network connectivity tests
- SSL certificate validation
- Model download tests
- Pipeline functionality tests
- Offline model validation

Results are saved to `transformer_diagnostics.json` and logged to `transformer_debug.log`.

### `test_transformers.py`

Performs basic functionality tests for transformer models.

```bash
python scripts/test_transformers.py
```

This script tests:
1. Loading the offline model
2. Downloading and using an online model
3. Running the NER pipeline with a standard model

## Proxy Management Scripts

### `proxy_service.py`

Controls the proxy service.

```bash
# Start the proxy
python scripts/proxy_service.py --start

# Stop the proxy
python scripts/proxy_service.py --stop

# Restart the proxy
python scripts/proxy_service.py --restart

# Check proxy status
python scripts/proxy_service.py --status
```

## Usage Example

Typical workflow for setting up transformers with the proxy:

```bash
# 1. Download transformer models before starting the proxy
python scripts/download_transformers_models.py --test

# 2. If there are issues, run the debug script
python scripts/debug_transformers.py

# 3. Start the proxy service
python scripts/proxy_service.py --start
```

## Troubleshooting

If you encounter issues:

1. Check the logs in the `logs/` directory
2. Run `debug_transformers.py` for detailed diagnostics
3. Refer to `docs/TRANSFORMER_SETUP.md` and `docs/TRANSFORMER_DEBUGGING.md` for solutions 