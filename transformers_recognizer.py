#!/usr/bin/env python3
"""
Transformers-based Recognizer for Presidio
Implements a recognizer that uses a Hugging Face transformer model (Piiranha) for PII detection
"""

import logging
import re
import sys
import warnings
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Pattern, Any

# Initialize global flags
IMPORTS_AVAILABLE = False
NUMPY_COMPATIBILITY_ISSUE = False
TRANSFORMERS_IMPORT_ERROR = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("transformers-recognizer")

# Try importing required libraries with robust error handling
try:
    from presidio_analyzer import RecognizerResult, EntityRecognizer, AnalysisExplanation
    from presidio_analyzer.nlp_engine import NlpArtifacts
    
    # Try importing transformers with numpy compatibility check
    try:
        # Filter numpy warnings that might occur during import
        warnings.filterwarnings('ignore', message='numpy.dtype size changed')
        warnings.filterwarnings('ignore', message='numpy.ufunc size changed')
        
        # Try to import transformers
        from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
        
        # Check accelerate version to avoid the 'remove_duplicate' parameter error
        try:
            import accelerate
            accelerate_version = accelerate.__version__
            logger.info(f"Using accelerate version: {accelerate_version}")
            # If accelerate version is too new, warn about it
            if accelerate_version > "0.20.3":
                logger.warning(f"Accelerate version {accelerate_version} may not be compatible with transformers 4.30.2")
                logger.warning("Consider downgrading: pip install accelerate==0.20.3")
        except ImportError:
            logger.info("Accelerate not imported directly, using version bundled with transformers")
        
        IMPORTS_AVAILABLE = True
        logger.info("Successfully imported transformers and presidio libraries")
    except ImportError as e:
        TRANSFORMERS_IMPORT_ERROR = str(e)
        if "numpy.dtype size changed" in str(e) or "binary incompatibility" in str(e):
            logger.warning(f"Numpy compatibility issue detected: {str(e)}")
            logger.warning("Consider using numpy==1.23.5 which is known to work with transformers==4.30.2")
            NUMPY_COMPATIBILITY_ISSUE = True
        elif "torch" in str(e):
            logger.warning(f"PyTorch compatibility issue detected: {str(e)}")
            logger.warning("Check for conflicts between torch versions in requirements.txt and requirements-privacy.txt")
        else:
            logger.warning(f"Error importing transformers: {str(e)}")
        IMPORTS_AVAILABLE = False
except ImportError as e:
    logger.warning(f"Required presidio libraries not available: {str(e)}")
    IMPORTS_AVAILABLE = False

# Define regex patterns for fallback entity recognition
REGEX_PATTERNS = {
    "EMAIL_ADDRESS": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "PHONE_NUMBER": re.compile(r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
    "IP_ADDRESS": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
    "US_SSN": re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'),
    "CREDIT_CARD": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    "URL": re.compile(r'\bhttps?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'),
    "DATE": re.compile(r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b'),
    "USERNAME": re.compile(r'\b@[A-Za-z0-9_]{3,15}\b'),
}

# Add additional regex patterns for common PII types
ADDITIONAL_REGEX_PATTERNS = {
    "ADDRESS": re.compile(r'\b\d+\s+[A-Za-z0-9\s,]+(?:Avenue|Lane|Road|Boulevard|Drive|Street|Ave|Dr|Rd|Blvd|Ln|St)\.?\b', re.IGNORECASE),
    "PERSON": re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'),
    "LOCATION": re.compile(r'\b[A-Z][a-z]+(?:,\s+[A-Z]{2})?\b'),
    "ORGANIZATION": re.compile(r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)+\s+(?:Inc|LLC|Ltd|Corporation|Corp|Company|Co)\b'),
    "PASSWORD": re.compile(r'\b(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}\b'),
}

# Update the REGEX_PATTERNS dictionary with additional patterns
REGEX_PATTERNS.update(ADDITIONAL_REGEX_PATTERNS)

# Try to import the offline model for fallback without downloading
try:
    sys.path.append(str(Path(__file__).parent / "models" / "dist"))
    import offline_model
    OFFLINE_MODEL_AVAILABLE = True
    logger.info("Offline model is available for fallback")
except ImportError:
    OFFLINE_MODEL_AVAILABLE = False
    logger.warning("Offline model not available for fallback")

class TransformersRecognizer(EntityRecognizer):
    """
    Recognizer that uses Hugging Face transformer models for PII detection.
    
    This recognizer leverages state-of-the-art models like Piiranha for more accurate
    and comprehensive PII detection capabilities.
    """
    
    def __init__(
        self,
        model_name: str = "dslim/bert-base-NER",  # Changed default to a more reliable model
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
        # Check if we can use the recognizer
        if not supported_entities:
            supported_entities = [
                "PERSON", "LOCATION", "ORGANIZATION", 
                "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", 
                "CREDIT_CARD", "IP_ADDRESS", "PASSWORD", 
                "USERNAME", "ADDRESS", "DATE", "URL"
            ]
            
        # Verify if we can use regex fallback for the requested entities
        if not IMPORTS_AVAILABLE and not self._has_regex_fallback(supported_entities):
            raise ImportError(
                "Required libraries not available for TransformersRecognizer and no regex fallback available. "
                f"Import error: {TRANSFORMERS_IMPORT_ERROR}"
            )
        
        # Log warning if using regex fallback
        if not IMPORTS_AVAILABLE:
            logger.warning("Using regex-based fallback for entity recognition due to import issues")
            if NUMPY_COMPATIBILITY_ISSUE:
                logger.warning("Numpy compatibility issue detected - consider using numpy==1.23.5 with transformers==4.30.2")
            
        self.model_name = model_name
        self.fallback_model = fallback_model
        
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
        
    def _get_local_model_path(self, model_name: str) -> Optional[Path]:
        """
        Check if a local copy of the model exists in the models directory.
        
        Args:
            model_name: Name of the model to check for
            
        Returns:
            Path to the local model directory or None if not found
        """
        # Extract model short name from full path
        short_name = model_name.split("/")[-1]
        
        # Check local models directory
        local_model_path = Path("models") / short_name
        if local_model_path.exists() and (local_model_path / "config.json").exists():
            logger.info(f"Found local model at {local_model_path}")
            return local_model_path
            
        # Check if we're running in a local directory with the model
        current_model_path = Path(short_name)
        if current_model_path.exists() and (current_model_path / "config.json").exists():
            logger.info(f"Found local model at {current_model_path}")
            return current_model_path
            
        return None
    
    def _has_regex_fallback(self, entities: List[str]) -> bool:
        """
        Check if we have regex patterns for the requested entities
        
        Args:
            entities: List of entity types to check
            
        Returns:
            True if at least one entity has a regex pattern, False otherwise
        """
        if not entities:
            return False
            
        has_patterns = any(entity in REGEX_PATTERNS for entity in entities)
        if has_patterns:
            available_entities = [entity for entity in entities if entity in REGEX_PATTERNS]
            logger.info(f"Regex fallback available for entities: {', '.join(available_entities)}")
        else:
            logger.warning(f"No regex patterns available for requested entities: {', '.join(entities)}")
            
        return has_patterns
    
    def load_model(self):
        """
        Load the transformer model and tokenizer with graceful fallback
        
        This method attempts to load the primary model locally first, then tries to download,
        then falls back to a secondary model, and finally to regex-based detection.
        """
        self.model = None
        self.using_regex_fallback = False
        self.using_offline_model = False
        
        # Skip model loading if imports aren't available
        if not IMPORTS_AVAILABLE:
            logger.info("Skipping model loading due to import issues")
            logger.info(f"Import error details: {TRANSFORMERS_IMPORT_ERROR}")
            
            # Try to use offline model if available
            if OFFLINE_MODEL_AVAILABLE:
                logger.info("Using offline model for entity recognition")
                self.using_offline_model = True
                return
                
            self.using_regex_fallback = True
            return
            
        # Don't use proxy for model downloads
        env_vars_to_clear = ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]
        original_env = {}
        for var in env_vars_to_clear:
            if var in os.environ:
                original_env[var] = os.environ[var]
                os.environ[var] = ""
        
        try:
            # Try loading the primary model from local directory first
            primary_local_path = self._get_local_model_path(self.model_name)
            if primary_local_path:
                try:
                    logger.info(f"Loading transformer model from local path: {primary_local_path}")
                    
                    try:
                        self.tokenizer = AutoTokenizer.from_pretrained(str(primary_local_path))
                        model = AutoModelForTokenClassification.from_pretrained(str(primary_local_path))
                        self.model = pipeline("token-classification", model=model, tokenizer=self.tokenizer, aggregation_strategy="simple")
                        logger.info(f"Local model loaded successfully from {primary_local_path}")
                        return
                    except Exception as e:
                        logger.warning(f"Error loading local model from {primary_local_path}: {str(e)}")
                        # Continue to try online loading
                except Exception as e:
                    logger.warning(f"Unexpected error loading local model: {str(e)}")
                    # Continue to try online loading
            
            # Try loading the primary model from HuggingFace
            try:
                logger.info(f"Loading transformer model from HuggingFace: {self.model_name}")
                
                # Use a try-except block with specific error handling
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                    model = AutoModelForTokenClassification.from_pretrained(self.model_name)
                    self.model = pipeline("token-classification", model=model, tokenizer=self.tokenizer, aggregation_strategy="simple")
                    logger.info(f"Model {self.model_name} loaded successfully from HuggingFace")
                    return
                except OSError as e:
                    # Handle model download/loading errors
                    logger.warning(f"OS error loading model {self.model_name}: {str(e)}")
                    raise
                except ValueError as e:
                    # Handle model configuration errors
                    logger.warning(f"Value error loading model {self.model_name}: {str(e)}")
                    raise
                except Exception as e:
                    # Handle other errors
                    logger.warning(f"Unexpected error loading model {self.model_name}: {str(e)}")
                    raise
                    
            except Exception as e:
                logger.warning(f"Error loading primary model {self.model_name}: {str(e)}")
                logger.info(f"Falling back to {self.fallback_model}")
                
            # Try loading the fallback model from local directory
            fallback_local_path = self._get_local_model_path(self.fallback_model)
            if fallback_local_path:
                try:
                    logger.info(f"Loading fallback model from local path: {fallback_local_path}")
                    
                    try:
                        self.tokenizer = AutoTokenizer.from_pretrained(str(fallback_local_path))
                        model = AutoModelForTokenClassification.from_pretrained(str(fallback_local_path))
                        self.model = pipeline("ner", model=model, tokenizer=self.tokenizer, aggregation_strategy="simple")
                        logger.info(f"Local fallback model loaded successfully from {fallback_local_path}")
                        return
                    except Exception as e:
                        logger.warning(f"Error loading local fallback model from {fallback_local_path}: {str(e)}")
                        # Continue to try online loading
                except Exception as e:
                    logger.warning(f"Unexpected error loading local fallback model: {str(e)}")
                    # Continue to try online loading
                
            # Try loading the fallback model from HuggingFace
            try:
                # Use a try-except block with specific error handling
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(self.fallback_model)
                    model = AutoModelForTokenClassification.from_pretrained(self.fallback_model)
                    self.model = pipeline("ner", model=model, tokenizer=self.tokenizer, aggregation_strategy="simple")
                    logger.info(f"Fallback model {self.fallback_model} loaded successfully from HuggingFace")
                    return
                except OSError as e:
                    # Handle model download/loading errors
                    logger.warning(f"OS error loading fallback model {self.fallback_model}: {str(e)}")
                    raise
                except ValueError as e:
                    # Handle model configuration errors
                    logger.warning(f"Value error loading fallback model {self.fallback_model}: {str(e)}")
                    raise
                except Exception as e:
                    # Handle other errors
                    logger.warning(f"Unexpected error loading fallback model {self.fallback_model}: {str(e)}")
                    raise
                    
            except Exception as e:
                logger.error(f"Error loading fallback model: {str(e)}")
                
                # Try to use offline model if available
                if OFFLINE_MODEL_AVAILABLE:
                    logger.info("Using offline model for entity recognition")
                    self.using_offline_model = True
                    return
                    
                logger.warning("No model could be loaded - switching to regex fallback")
                self.using_regex_fallback = True
                self.model = None
        
        finally:
            # Restore original environment variables
            for var, value in original_env.items():
                os.environ[var] = value

    def _analyze_with_regex(self, text: str, entities: List[str]) -> List[RecognizerResult]:
        """
        Analyze text using regex patterns as a fallback mechanism.
        
        Args:
            text: The text to analyze
            entities: List of entities to look for
            
        Returns:
            List of RecognizerResult objects
        """
        results = []
        
        if not text:
            return results
            
        # Log that we're using regex fallback
        logger.debug(f"Using regex fallback for entities: {', '.join(entities)}")
        
        # Only process entities that have regex patterns
        for entity in entities:
            if entity in REGEX_PATTERNS:
                pattern = REGEX_PATTERNS[entity]
                try:
                    for match in pattern.finditer(text):
                        start, end = match.span()
                        matched_text = text[start:end]
                        
                        # Skip empty matches
                        if start == end:
                            continue
                            
                        # Validate match based on entity type
                        score = self._validate_regex_match(entity, matched_text)
                        
                        # Skip low confidence matches
                        if score < self.confidence_threshold:
                            continue
                        
                        # Create explanation
                        explanation = AnalysisExplanation(
                            recognizer=self.name,
                            original_score=score,
                            pattern_name=f"regex_{entity}",
                            pattern=pattern.pattern,
                            validation_result=None
                        )
                        
                        # Create result
                        result = RecognizerResult(
                            entity_type=entity,
                            start=start,
                            end=end,
                            score=score,
                            analysis_explanation=explanation
                        )
                        
                        results.append(result)
                except Exception as e:
                    logger.warning(f"Error in regex matching for {entity}: {str(e)}")
        
        if results:
            logger.info(f"Regex fallback found {len(results)} entities")
        else:
            logger.debug("No entities found with regex fallback")
            
        return results
    
    def _analyze_with_offline_model(self, text: str, entities: List[str]) -> List[RecognizerResult]:
        """
        Analyze text using the offline model.
        
        Args:
            text: The text to analyze
            entities: List of entities to look for
            
        Returns:
            List of RecognizerResult objects
        """
        results = []
        
        if not text or not OFFLINE_MODEL_AVAILABLE:
            return results
            
        # Log that we're using the offline model
        logger.debug(f"Using offline model for entities: {', '.join(entities)}")
        
        try:
            # Create offline model
            model = offline_model.OfflineModel()
            
            # Get predictions
            predictions = model(text)
            
            for prediction in predictions:
                # Get entity type, mapping to Presidio entity type if necessary
                entity_type = prediction["entity_group"]
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
                    pattern_name="offline_model",
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
                
            if results:
                logger.info(f"Offline model found {len(results)} entities")
            else:
                logger.debug("No entities found with offline model")
                
        except Exception as e:
            logger.error(f"Error in offline model analysis: {str(e)}")
            logger.info("Falling back to regex patterns")
            
            # Use regex fallback if offline model fails
            return self._analyze_with_regex(text, entities)
            
        return results
        
    def _validate_regex_match(self, entity_type: str, matched_text: str) -> float:
        """
        Validate a regex match and return a confidence score.
        
        Args:
            entity_type: The type of entity
            matched_text: The matched text
            
        Returns:
            Confidence score between 0 and 1
        """
        # Default confidence
        base_confidence = 0.85
        
        # Entity-specific validation logic
        if entity_type == "EMAIL_ADDRESS":
            # Check for common email domains for higher confidence
            common_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
            domain = matched_text.split('@')[-1].lower()
            return 0.95 if domain in common_domains else base_confidence
            
        elif entity_type == "PHONE_NUMBER":
            # More digits usually means higher confidence
            digit_count = sum(c.isdigit() for c in matched_text)
            return min(0.95, base_confidence + (digit_count - 10) * 0.01) if digit_count >= 10 else base_confidence
            
        elif entity_type == "IP_ADDRESS":
            # Validate IP address format
            try:
                octets = [int(o) for o in matched_text.split('.')]
                valid = all(0 <= o <= 255 for o in octets) and len(octets) == 4
                return 0.95 if valid else 0.7
            except:
                return 0.7
                
        elif entity_type == "US_SSN":
            # Check for valid SSN format (not 000-00-0000, etc.)
            if matched_text.replace('-', '') in ['000000000', '111111111', '999999999']:
                return 0.6
            return base_confidence
            
        elif entity_type == "CREDIT_CARD":
            # Apply Luhn algorithm for credit card validation
            digits = [int(d) for d in matched_text if d.isdigit()]
            if len(digits) < 13 or len(digits) > 19:
                return 0.7
            return 0.95 if self._luhn_check(digits) else 0.7
            
        # Default confidence for other entity types
        return base_confidence
        
    def _luhn_check(self, digits: List[int]) -> bool:
        """
        Implement the Luhn algorithm for credit card validation.
        
        Args:
            digits: List of digits in the credit card number
            
        Returns:
            True if valid according to Luhn algorithm, False otherwise
        """
        try:
            # Reverse the digits
            digits = digits[::-1]
            
            # Double every second digit
            doubled = [(d * 2 if i % 2 == 1 else d) for i, d in enumerate(digits)]
            
            # Sum the digits (if a doubled number is > 9, add its digits)
            total = sum(d if d < 10 else d - 9 for d in doubled)
            
            # Check if divisible by 10
            return total % 10 == 0
        except Exception:
            return False
    
    def analyze(
        self, text: str, entities: List[str], nlp_artifacts: NlpArtifacts = None
    ) -> List[RecognizerResult]:
        """
        Analyze text using the transformer model or fallback mechanisms to identify entities.
        
        Args:
            text: The text to analyze
            entities: List of entities to look for
            nlp_artifacts: NLP artifacts from NLP engine
            
        Returns:
            List of RecognizerResult objects
        """
        if not text:
            return []
        
        # Use regex fallback if specifically using regex fallback
        if self.using_regex_fallback:
            logger.info("Using regex fallback for entity recognition - transformers model unavailable")
            return self._analyze_with_regex(text, entities)
            
        # Use offline model if that's what we're using
        if self.using_offline_model:
            logger.info("Using offline model for entity recognition - transformers model unavailable")
            return self._analyze_with_offline_model(text, entities)
            
        # Use model if available
        if self.model:
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
                error_msg = str(e)
                logger.error(f"Error in transformer analysis: {error_msg}")
                
                # Check for specific error types
                if "CUDA" in error_msg or "GPU" in error_msg:
                    logger.warning("GPU/CUDA error detected - consider using CPU mode")
                elif "memory" in error_msg.lower():
                    logger.warning("Memory error detected - model may be too large for available memory")
                elif "numpy" in error_msg.lower():
                    logger.warning("Numpy compatibility issue detected during inference")
                    logger.warning("Consider using numpy==1.23.5 which is known to work with transformers==4.30.2")
                elif "named_parameters" in error_msg and "remove_duplicate" in error_msg:
                    logger.warning("Accelerate compatibility issue detected - downgrade accelerate: pip install accelerate==0.20.3")
                
                logger.info("Falling back to alternative entity recognition method")
                
                # Try to recover on future calls by re-initializing the model
                try:
                    logger.info("Attempting to reinitialize model...")
                    self.load_model()
                except Exception as reinit_error:
                    logger.error(f"Failed to reinitialize model: {str(reinit_error)}")
                    logger.warning("Permanently switching to fallback for this session")
                    self.using_regex_fallback = True
                
                # Try offline model first if available
                if OFFLINE_MODEL_AVAILABLE:
                    logger.info("Using offline model for this request")
                    return self._analyze_with_offline_model(text, entities)
                    
                # Otherwise use regex fallback for this call
                return self._analyze_with_regex(text, entities)
            
            # If no results from transformer model, try regex fallback
            if not results:
                logger.info("No results from transformer model, trying regex fallback")
                regex_results = self._analyze_with_regex(text, entities)
                
                if regex_results:
                    logger.info(f"Regex fallback found {len(regex_results)} entities")
                    results.extend(regex_results)
                else:
                    logger.debug("No entities found with regex fallback either")
                
            return results
        else:
            # We shouldn't get here normally, but just in case
            logger.warning("No model loaded and not using fallback - trying regex fallback")
            return self._analyze_with_regex(text, entities)

# Register the recognizer with Presidio analyzer when imported
def register_with_presidio(analyzer):
    """Register the TransformersRecognizer with a Presidio analyzer instance"""
    try:
        # Create and register the recognizer
        transformers_recognizer = TransformersRecognizer()
        analyzer.registry.add_recognizer(transformers_recognizer)
        
        if transformers_recognizer.model is not None:
            logger.info("TransformersRecognizer registered successfully with Presidio using transformer models")
        elif transformers_recognizer.using_offline_model:
            logger.info("TransformersRecognizer registered with Presidio using offline model")
        else:
            logger.warning("TransformersRecognizer registered with Presidio using regex fallback due to model loading issues")
            if NUMPY_COMPATIBILITY_ISSUE:
                logger.warning("Numpy compatibility issue detected - consider using numpy==1.23.5 with transformers==4.30.2")
            logger.info(f"Import error details: {TRANSFORMERS_IMPORT_ERROR}")
        
        return True
    except ImportError as e:
        logger.error(f"Error registering TransformersRecognizer (import error): {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error registering TransformersRecognizer: {str(e)}")
        return False

# Diagnostic function to check environment compatibility
def check_environment_compatibility():
    """
    Check if the environment is compatible with transformers and numpy
    
    Returns:
        Dictionary with environment information
    """
    import platform
    import os
    
    env_info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "numpy_available": False,
        "numpy_version": None,
        "transformers_available": False,
        "transformers_version": None,
        "torch_available": False,
        "torch_version": None,
        "accelerate_available": False,
        "accelerate_version": None,
        "compatible_numpy_version": "1.23.5",  # Known compatible version
        "compatible_transformers_version": "4.30.2",  # Known compatible version
        "compatible_accelerate_version": "0.20.3",  # Known compatible version
        "import_errors": [],
    }
    
    # Check numpy
    try:
        import numpy as np
        env_info["numpy_available"] = True
        env_info["numpy_version"] = np.__version__
        
        # Check if numpy version is compatible
        if env_info["numpy_version"] != env_info["compatible_numpy_version"]:
            logger.warning(f"Current numpy version {env_info['numpy_version']} may not be compatible. "
                          f"Consider using version {env_info['compatible_numpy_version']}")
    except ImportError as e:
        env_info["import_errors"].append(f"Numpy import error: {str(e)}")
    
    # Check transformers
    try:
        import transformers
        env_info["transformers_available"] = True
        env_info["transformers_version"] = transformers.__version__
        
        # Check if transformers version is compatible
        if env_info["transformers_version"] != env_info["compatible_transformers_version"]:
            logger.warning(f"Current transformers version {env_info['transformers_version']} may not be compatible. "
                          f"Consider using version {env_info['compatible_transformers_version']}")
    except ImportError as e:
        env_info["import_errors"].append(f"Transformers import error: {str(e)}")
    
    # Check torch
    try:
        import torch
        env_info["torch_available"] = True
        env_info["torch_version"] = torch.__version__
    except ImportError as e:
        env_info["import_errors"].append(f"PyTorch import error: {str(e)}")
    
    # Check accelerate
    try:
        import accelerate
        env_info["accelerate_available"] = True
        env_info["accelerate_version"] = accelerate.__version__
        
        # Check if accelerate version is compatible
        if env_info["accelerate_version"] != env_info["compatible_accelerate_version"]:
            logger.warning(f"Current accelerate version {env_info['accelerate_version']} may not be compatible. "
                          f"Consider using version {env_info['compatible_accelerate_version']}")
    except ImportError as e:
        env_info["import_errors"].append(f"Accelerate import error: {str(e)}")
    
    # Check for potential conflicts in requirements files
    try:
        import pkg_resources
        
        # Check for conflicts between requirements files
        req_files = ["requirements.txt", "requirements-privacy.txt"]
        requirements = {}
        
        for req_file in req_files:
            if os.path.exists(req_file):
                with open(req_file, 'r') as f:
                    requirements[req_file] = f.read()
                    
        # Check for torch version conflicts
        torch_versions = []
        for req_file, content in requirements.items():
            for line in content.splitlines():
                if line.strip().startswith("torch=="):
                    torch_versions.append((req_file, line.strip()))
        
        if len(torch_versions) > 1:
            logger.warning(f"Multiple torch versions specified in requirements files: {torch_versions}")
            env_info["torch_version_conflict"] = torch_versions
            
    except Exception as e:
        logger.warning(f"Error checking requirements files: {str(e)}")
    
    logger.info(f"Environment compatibility check: {env_info}")
    return env_info