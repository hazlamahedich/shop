"""Intent classification services for natural language processing."""

from app.services.intent.classification_schema import (
    ClassificationResult,
    ExtractedEntities,
    IntentType,
    to_camel,
)
from app.services.intent.intent_classifier import IntentClassifier
from app.services.intent.prompt_templates import get_classification_system_prompt
from app.services.intent.variation_maps import (
    normalize_message,
    normalize_brand,
    get_product_category,
    get_all_product_terms,
)

__all__ = [
    "ClassificationResult",
    "ExtractedEntities",
    "IntentType",
    "IntentClassifier",
    "get_classification_system_prompt",
    "normalize_message",
    "normalize_brand",
    "get_product_category",
    "get_all_product_terms",
    "to_camel",
]
