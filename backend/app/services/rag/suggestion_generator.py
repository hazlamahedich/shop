"""Suggestion generator for follow-up questions from RAG context.

Story 10-3: Quick Reply Chips Widget

Generates relevant follow-up question suggestions based on:
1. RAG chunk content (topic extraction)
2. Fallback to keyword-based category detection
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import structlog

from app.services.rag.retrieval_service import RetrievedChunk

logger = structlog.get_logger(__name__)


@dataclass
class SuggestionConfig:
    """Configuration for suggestion generation."""

    max_suggestions: int = 4
    min_chunk_content_length: int = 20


FALLBACK_SUGGESTIONS: dict[str, list[str]] = {
    "pricing": [
        "What are your pricing plans?",
        "Do you offer discounts?",
        "Are there any promotions available?",
        "Can I get a quote?",
    ],
    "hours": [
        "What are your business hours?",
        "Are you open on weekends?",
        "When can I visit?",
        "Do you offer after-hours support?",
    ],
    "contact": [
        "How can I contact support?",
        "Do you have a phone number?",
        "Can I schedule a call?",
        "Where are you located?",
    ],
    "features": [
        "What features do you offer?",
        "How does it work?",
        "Can I see a demo?",
        "What's included?",
    ],
    "default": [
        "Can you tell me more?",
        "What else should I know?",
        "Do you have documentation?",
        "How can I get started?",
    ],
}

KEYWORD_CATEGORIES: dict[str, list[str]] = {
    "pricing": [
        "price",
        "cost",
        "pay",
        "discount",
        "cheap",
        "expensive",
        "afford",
        "budget",
        "fee",
        "rate",
    ],
    "hours": ["hour", "open", "close", "time", "schedule", "available", "when"],
    "contact": ["contact", "phone", "email", "reach", "call", "support", "help", "talk"],
    "features": ["feature", "how", "work", "demo", "include", "offer", "provide", "service"],
}


class SuggestionGenerator:
    """Generate follow-up question suggestions from RAG context.

    Story 10-3: Quick Reply Chips Widget

    Features:
    - Topic extraction from RAG chunk content
    - Document name-based suggestions
    - Keyword-based category detection for fallback
    - Max 4 suggestions per response
    """

    def __init__(self, config: SuggestionConfig | None = None):
        """Initialize suggestion generator.

        Args:
            config: Optional configuration for suggestion generation
        """
        self.config = config or SuggestionConfig()

    async def generate_suggestions(
        self,
        query: str,
        chunks: list[RetrievedChunk] | None,
    ) -> list[str]:
        """Generate follow-up questions based on RAG context.

        Args:
            query: User's original query
            chunks: Retrieved RAG chunks (may be empty or None)

        Returns:
            List of follow-up question suggestions (max 4)
        """
        if chunks and len(chunks) > 0:
            return self._extract_from_chunks(chunks)

        return self._fallback_suggestions(query)

    def _extract_from_chunks(self, chunks: list[RetrievedChunk]) -> list[str]:
        """Extract suggestions from RAG chunk content.

        Strategy:
        1. Use document names as basis for "Tell me more about X"
        2. Extract key topics from content (capitalized phrases)
        3. Generate "What about X?" questions

        Args:
            chunks: Retrieved RAG chunks

        Returns:
            List of suggestions (max 4)
        """
        suggestions: list[str] = []
        seen_suggestions: set[str] = set()

        for chunk in chunks[:2]:
            doc_name = self._clean_document_name(chunk.document_name)
            if doc_name:
                suggestion = f"Tell me more about {doc_name}"
                if suggestion.lower() not in seen_suggestions:
                    suggestions.append(suggestion)
                    seen_suggestions.add(suggestion.lower())

        topics = self._extract_topics(chunks)
        for topic in topics:
            if len(suggestions) >= self.config.max_suggestions:
                break
            suggestion = f"What about {topic}?"
            if suggestion.lower() not in seen_suggestions:
                suggestions.append(suggestion)
                seen_suggestions.add(suggestion.lower())

        while len(suggestions) < self.config.max_suggestions:
            default_suggestions = FALLBACK_SUGGESTIONS["default"]
            for default in default_suggestions:
                if len(suggestions) >= self.config.max_suggestions:
                    break
                if default.lower() not in seen_suggestions:
                    suggestions.append(default)
                    seen_suggestions.add(default.lower())
            break

        return suggestions[: self.config.max_suggestions]

    def _clean_document_name(self, document_name: str) -> str | None:
        """Clean document name for use in suggestions.

        Args:
            document_name: Original document filename

        Returns:
            Cleaned name suitable for display, or None if not useful
        """
        name = document_name
        for ext in [".pdf", ".txt", ".md", ".doc", ".docx"]:
            name = name.replace(ext, "")
        name = name.replace("_", " ").replace("-", " ")
        name = re.sub(r"\s+", " ", name).strip()
        if len(name) < 3 or name.lower() in ["document", "file", "untitled", "readme"]:
            return None
        return name

    def _extract_topics(self, chunks: list[RetrievedChunk]) -> list[str]:
        """Extract key topics from chunk content.

        MVP: Simple capitalized phrase extraction
        Future: Use LLM for better topic extraction

        Args:
            chunks: Retrieved RAG chunks

        Returns:
            List of extracted topics
        """
        topics: list[str] = []
        seen_topics: set[str] = set()

        for chunk in chunks:
            content = chunk.content
            if len(content) < self.config.min_chunk_content_length:
                continue
            matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", content)
            for match in matches:
                topic = match.strip()
                skip_words = {
                    "The",
                    "This",
                    "That",
                    "These",
                    "Those",
                    "What",
                    "When",
                    "Where",
                    "How",
                    "Why",
                    "If",
                    "Then",
                    "Else",
                    "And",
                    "But",
                    "Or",
                    "For",
                    "With",
                    "From",
                    "Into",
                    "Upon",
                }
                if topic in skip_words:
                    continue
                if len(topic) < 4:
                    continue
                if topic.lower() not in seen_topics:
                    topics.append(topic)
                    seen_topics.add(topic.lower())
                if len(topics) >= 4:
                    break
            if len(topics) >= 4:
                break

        return topics

    def _fallback_suggestions(self, query: str) -> list[str]:
        """Generate fallback suggestions based on query keywords.

        Args:
            query: User's original query

        Returns:
            List of category-based suggestions (max 4)
        """
        category = self._detect_category(query)
        suggestions = FALLBACK_SUGGESTIONS.get(category, FALLBACK_SUGGESTIONS["default"])
        return suggestions[: self.config.max_suggestions]

    def _detect_category(self, query: str) -> str:
        """Detect conversation category from query keywords.

        Args:
            query: User's query text

        Returns:
            Category name (pricing, hours, contact, features, or default)
        """
        query_lower = query.lower()

        for category, keywords in KEYWORD_CATEGORIES.items():
            if any(kw in query_lower for kw in keywords):
                return category

        return "default"
