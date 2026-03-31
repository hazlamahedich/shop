"""Base context extractor for conversation context memory.

Story 11-1: Conversation Context Memory
Defines the interface for mode-specific context extractors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseContextExtractor(ABC):
    """Base class for mode-specific context extractors.

    Each bot mode (ecommerce, general) has its own extractor
    that identifies and extracts relevant context from user messages.
    """

    @abstractmethod
    async def extract(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Extract context from user message and merge with existing context.

        Args:
            message: User message to extract context from
            context: Current conversation context

        Returns:
            Updated context with new information extracted
        """
        pass

    def _merge_context(self, base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
        """Merge updates into base context.

        Args:
            base: Base context dictionary
            updates: Updates to apply

        Returns:
            Merged context
        """
        result = base.copy()

        for key, value in updates.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                # Recursively merge nested dictionaries
                result[key] = self._merge_context(result[key], value)
            elif isinstance(value, list) and key in result and isinstance(result[key], list):
                # Append to lists, avoiding duplicates
                # Handle lists of simple types (int, str) and lists of dicts
                if result[key] and isinstance(result[key][0], dict):
                    # For lists of dicts, compare by specific field (e.g., 'type' or 'id')
                    existing_keys = self._extract_dict_keys(result[key], 'type')
                    for item in value:
                        if isinstance(item, dict) and 'type' in item:
                            if item['type'] not in existing_keys:
                                result[key].append(item)
                                existing_keys.add(item['type'])
                        else:
                            # No type field, just append
                            result[key].append(item)
                else:
                    # For lists of simple types (int, str)
                    existing = set(result[key])
                    for item in value:
                        if item not in existing:
                            result[key].append(item)
                            existing.add(item)
            else:
                # Override with new value
                result[key] = value

        return result

    def _extract_dict_keys(self, dict_list: list[dict], key: str) -> set[Any]:
        """Extract unique values from a list of dicts.

        Args:
            dict_list: List of dictionaries
            key: Key to extract

        Returns:
            Set of unique values
        """
        return {item.get(key) for item in dict_list if isinstance(item, dict) and key in item}
