#!/usr/bin/env python3
"""
Transformers-based Recognizer for Presidio
Implements a recognizer that uses a Hugging Face transformer model (Piiranha) for PII detection
"""

import logging
import re
from typing import List, Optional, Tuple

try:
    from presidio_analyzer import RecognizerResult, EntityRecognizer, AnalysisExplanation
    from presidio_analyzer.nlp_engine import NlpArtifacts
    from transformers import pipeline, AutoTokenizer
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    logging.warning("Required libraries not available. TransformersRecognizer will not be functional.")

logger = logging.getLogger("transformers-recognizer")

class TransformersRecognizer(EntityRecognizer):
    """
    Recognizer that uses Hugging Face transformer models for PII detection.
    
    This recognizer leverages state-of-the-art models like Piiranha for more accurate
    and comprehensive PII detection capabilities.
    """
    
    def __init__(
        self,
        model_name: str = "iiiorg/piiranha-v1-detect-personal-information",
        fallback_model: str = "dslim/bert-base-NER",
        supported_entities: Optional[List[str]] = None,
        supported_language: str = "en",
        confidence_threshold: float = 0.7,
    ):
        """
        Initialize the TransformersRecognizer.
        
        Args:
            model_name: Name of the Hugging Face model to use
            fallback_model: Fallback model to use if the main model fails to load
            supported_entities: List of entity types this recognizer supports
            supported_language: Language supported by this recognizer
            confidence_threshold: Minimum confidence threshold to return matches
        """
        if not IMPORTS_AVAILABLE:
            raise ImportError("Required libraries not available for TransformersRecognizer")
            
        self.model_name = model_name
        self.fallback_model = fallback_model
        
        # Define default entities if none provided
        if not supported_entities:
            supported_entities = [
                "PERSON", "LOCATION", "ORGANIZATION", 
                "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", 
                "CREDIT_CARD", "IP_ADDRESS", "PASSWORD", 
                "USERNAME", "ADDRESS", "DATE", "URL"
            ]
        
        # Initialize the recognizer
        super().__init__(
            supported_entities=supported_entities,
            supported_language=supported_language,
            name="TransformersRecognizer",
        )
        
        self.confidence_threshold = confidence_threshold
        self.load_model()
        
        # Map model entity types to Presidio entity types
        self.entity_mapping = {
            "PERSON": "PERSON",
            "PER": "PERSON",
            "PERSON_NAME": "PERSON",
            "ORG": "ORGANIZATION",
            "ORGANIZATION": "ORGANIZATION",
            "LOC": "LOCATION",
            "LOCATION": "LOCATION",
            "EMAIL": "EMAIL_ADDRESS",
            "EMAIL_ADDRESS": "EMAIL_ADDRESS",
            "PHONE": "PHONE_NUMBER",
            "PHONE_NUMBER": "PHONE_NUMBER",
            "SSN": "US_SSN",
            "US_SSN": "US_SSN",
            "CREDIT_CARD": "CREDIT_CARD",
            "CC": "CREDIT_CARD",
            "IP_ADDRESS": "IP_ADDRESS",
            "IP": "IP_ADDRESS",
            "PASSWORD": "PASSWORD",
            "USER": "USERNAME",
            "USERNAME": "USERNAME",
            "ADDRESS": "ADDRESS",
            "DATE": "DATE",
            "URL": "URL"
        }
    
    def load_model(self):
        """Load the transformer model and tokenizer with graceful fallback"""
        self.model = None
        
        # Try loading the primary model
        try:
            logger.info(f"Loading transformer model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = pipeline("token-classification", model=self.model_name, aggregation_strategy="simple")
            logger.info(f"Model {self.model_name} loaded successfully")
            return
        except Exception as e:
            logger.warning(f"Error loading primary model {self.model_name}: {str(e)}")
            logger.info(f"Falling back to {self.fallback_model}")
            
        # Try loading the fallback model
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.fallback_model)
            self.model = pipeline("ner", model=self.fallback_model, aggregation_strategy="simple")
            logger.info(f"Fallback model {self.fallback_model} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading fallback model: {str(e)}")
            logger.error("No model could be loaded - recognizer will not function properly")
            self.model = None
    
    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        """
        Analyze text using the transformer model to identify entities.
        
        Args:
            text: The text to analyze
            entities: List of entities to look for
            nlp_artifacts: NLP artifacts from NLP engine
            
        Returns:
            List of RecognizerResult objects
        """
        if not text or not self.model:
            return []
        
        results = []
        
        try:
            # Get predictions from the model
            predictions = self.model(text)
            
            for prediction in predictions:
                # Get entity type, mapping to Presidio entity type if necessary
                entity_type = prediction["entity_group"].upper()
                score = prediction["score"]
                start = prediction["start"]
                end = prediction["end"]
                
                # Skip if confidence is too low
                if score < self.confidence_threshold:
                    continue
                
                # Map to standardized entity type
                mapped_entity = self.entity_mapping.get(entity_type, entity_type)
                
                # Skip if not in requested entities
                if mapped_entity not in entities:
                    continue
                
                # Create explanation
                explanation = AnalysisExplanation(
                    recognizer=self.name,
                    original_score=score,
                    pattern_name=f"transformer_{self.model_name}",
                    pattern="",
                    validation_result=None
                )
                
                # Create result
                result = RecognizerResult(
                    entity_type=mapped_entity,
                    start=start,
                    end=end,
                    score=score,
                    analysis_explanation=explanation
                )
                
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error in transformer analysis: {str(e)}")
            # Try to recover on future calls by re-initializing the model
            try:
                logger.info("Attempting to reinitialize model...")
                self.load_model()
            except Exception:
                pass
        
        return results

# Register the recognizer with Presidio analyzer when imported
def register_with_presidio(analyzer):
    """Register the TransformersRecognizer with a Presidio analyzer instance"""
    if not IMPORTS_AVAILABLE:
        logger.warning("Cannot register TransformersRecognizer: Required libraries not available")
        return False
    
    try:
        # Create and register the recognizer
        transformers_recognizer = TransformersRecognizer()
        analyzer.registry.add_recognizer(transformers_recognizer)
        logger.info("TransformersRecognizer registered successfully with Presidio")
        return True
    except Exception as e:
        logger.error(f"Error registering TransformersRecognizer: {str(e)}")
        return False