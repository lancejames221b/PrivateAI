# Piiranha Integration for Enhanced PII Detection

This document describes the integration of the Piiranha transformer model with Microsoft Presidio in the Private AI system.

## Overview

The Private AI system now integrates the state-of-the-art Piiranha model from Hugging Face to enhance PII detection capabilities. This integration combines the strengths of both approaches:

1. **Microsoft Presidio**: Provides the robust framework, pattern-based detection, and validation
2. **Piiranha Transformer Model**: Contributes enhanced accuracy for unstructured PII detection

## The Piiranha Model

**iiiorg/piiranha-v1-detect-personal-information** is a specialized transformer model fine-tuned for PII detection:

- Based on microsoft/mdeberta-v3-base architecture
- 99.44% overall accuracy on PII detection tasks
- Excellent performance for detecting emails, names, addresses, and more
- Multilingual support (English, Spanish, French, German, Italian, Dutch)
- Better at contextual understanding than pattern-based approaches

## Implementation Details

The integration uses a custom `TransformersRecognizer` class that implements Presidio's `EntityRecognizer` interface:

```python
class TransformersRecognizer(EntityRecognizer):
    """Recognizer that uses Hugging Face transformer models for PII detection."""
    
    def __init__(self, model_name="iiiorg/piiranha-v1-detect-personal-information", ...):
        # Initialize model and mapping
        
    def analyze(self, text, entities, nlp_artifacts=None):
        # Use transformer model to detect entities
        # Map detected entities to Presidio entity types
        # Return RecognizerResult objects
```

This recognizer is registered with the Presidio analyzer engine:

```python
# Register the custom recognizer
transformers_recognizer = TransformersRecognizer(model_name="iiiorg/piiranha-v1-detect-personal-information")
analyzer.registry.add_recognizer(transformers_recognizer)
```

## Configuration

The transformer model can be configured via environment variables in `.env`:

```
# Modern PII detection model configuration
TRANSFORMER_MODEL_NAME=iiiorg/piiranha-v1-detect-personal-information
```

You can replace this with any compatible Hugging Face token classification model.

## Performance Considerations

- The transformer model requires more computational resources than pattern-based detection
- First initialization may take longer as the model is downloaded from Hugging Face
- For resource-constrained environments, you may want to use a smaller model
- The hybrid approach improves recall but may impact processing speed

## Testing and Validation

Use the included test script to compare the performance of the standard Presidio detection with the enhanced Piiranha model:

```bash
python test_enhanced_pii.py
```

The test demonstrates the improved detection capabilities on real-world examples.

## Future Improvements

- Add GPU acceleration support for faster inference
- Implement model quantization for reduced memory footprint
- Fine-tune the model on domain-specific PII for your use case
- Add more mappings between model entity types and Presidio entity types