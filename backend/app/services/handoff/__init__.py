"""Handoff detection service for human assistance triggers."""

from app.services.handoff.detector import (
    CONFIDENCE_THRESHOLD,
    CONFIDENCE_TRIGGER_COUNT,
    HANDOFF_KEYWORDS,
    LOOP_TRIGGER_COUNT,
    HandoffDetector,
)

__all__ = [
    "HandoffDetector",
    "HANDOFF_KEYWORDS",
    "CONFIDENCE_THRESHOLD",
    "CONFIDENCE_TRIGGER_COUNT",
    "LOOP_TRIGGER_COUNT",
]
