"""Base schema with common configuration for all API schemas.

Provides consistent camelCase alias generation and populate_by_name behavior
across all schema classes following the Minimal Envelope pattern.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase for JSON serialization.

    Args:
        string: The snake_case string to convert

    Returns:
        The camelCase version of the string

    Examples:
        >>> to_camel("request_id")
        'requestId'
        >>> to_camel("created_at")
        'createdAt'
        >>> to_camel("webhook_url")
        'webhookUrl'
    """
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class BaseSchema(BaseModel):
    """Base schema with common configuration for all API schemas.

    Provides:
    - Automatic camelCase alias generation for JSON serialization
    - populate_by_name enabled for both camelCase and snake_case input
    - serialize_by_alias enabled for automatic camelCase output
    - Consistent behavior across all schema classes

    All request/response schemas should extend this class to maintain
    consistent API contract with frontend (JavaScript conventions).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class MinimalEnvelope(BaseSchema):
    """Minimal envelope pattern for API responses.

    Structure: {data: {...}, meta: {requestId, timestamp}}
    Follows project architecture pattern for consistent API responses.

    Attributes:
        data: Response payload (any type)
        meta: Response metadata with requestId and timestamp
    """

    data: Any
    meta: MetaData


class MetaData(BaseSchema):
    """Metadata for API responses following Minimal Envelope pattern.

    Includes request_id for tracing and ISO-8601 timestamp.

    Attributes:
        request_id: Unique request identifier for distributed tracing
        timestamp: ISO-8601 timestamp of response generation
    """

    request_id: str
    timestamp: str


__all__ = [
    "BaseSchema",
    "MinimalEnvelope",
    "MetaData",
    "to_camel",
]
