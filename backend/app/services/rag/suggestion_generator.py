"""Suggestion generator for follow-up questions from RAG context.

Story 10-3: Quick Reply Chips Widget

Generates relevant follow-up question suggestions based on:
1. LLM-powered generation (when LLM service available)
2. RAG chunk content (topic extraction)
3. Fallback to keyword-based category detection
"""

from __future__ import annotations

import json
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
    llm_temperature: float = 0.5
    llm_max_tokens: int = 200


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
    - LLM-powered suggestion generation (primary)
    - Topic extraction from RAG chunk content (fallback)
    - Document name-based suggestions
    - Keyword-based category detection for fallback
    - Max 4 suggestions per response
    """

    def __init__(
        self,
        config: SuggestionConfig | None = None,
        llm_service=None,
    ):
        """Initialize suggestion generator.

        Args:
            config: Optional configuration for suggestion generation
            llm_service: Optional LLM service for better suggestions
        """
        self.config = config or SuggestionConfig()
        self.llm_service = llm_service

    async def generate_suggestions(
        self,
        query: str,
        chunks: list[RetrievedChunk] | None,
    ) -> list[str]:
        """Generate follow-up questions based on RAG context.

        Priority:
        1. LLM-based generation (if LLM service available and chunks exist)
        2. Topic extraction from chunks
        3. Keyword-based fallback

        Args:
            query: User's original query
            chunks: Retrieved RAG chunks (may be empty or None)

        Returns:
            List of follow-up question suggestions (max 4)
        """
        if chunks and len(chunks) > 0:
            if self.llm_service:
                llm_suggestions = await self._generate_with_llm(query, chunks)
                if llm_suggestions:
                    return llm_suggestions
            return self._extract_from_chunks(chunks)

        return self._fallback_suggestions(query)

    async def _generate_with_llm(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[str] | None:
        """Use LLM to generate contextual follow-up questions.

        Args:
            query: User's original query
            chunks: Retrieved RAG chunks for context

        Returns:
            List of suggestions from LLM, or None if generation failed
        """
        if not self.llm_service:
            return None

        context_text = self._build_context_from_chunks(chunks)

        prompt = f"""Based on the user's question and the relevant context, generate {self.config.max_suggestions} follow-up questions the user might want to ask next.

User's question: {query}

Context from knowledge base:
{context_text}

Requirements:
1. Questions must be DIRECTLY related to the context provided
2. Questions should help the user explore the topic deeper
3. Each question should be specific and actionable
4. Questions should be natural, conversational (not robotic)
5. DO NOT repeat the original question
6. DO NOT ask generic questions like "Can you tell me more?"

Return ONLY a JSON array of {self.config.max_suggestions} question strings.
Example: ["What are your business hours?", "How can I contact support?", "Do you offer discounts?", "Where are you located?"]"""

        try:
            from app.services.llm.base_llm_service import LLMMessage

            messages = [LLMMessage(role="user", content=prompt)]
            response = await self.llm_service.chat(
                messages=messages,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
            )

            content = response.content.strip()

            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            suggestions = json.loads(content)

            if isinstance(suggestions, list):
                valid_suggestions = [
                    s for s in suggestions if isinstance(s, str) and len(s.strip()) > 5
                ]
                return valid_suggestions[: self.config.max_suggestions]

        except json.JSONDecodeError as e:
            logger.debug("suggestion_llm_json_parse_failed", error=str(e))
        except Exception as e:
            logger.warning("suggestion_llm_generation_failed", error=str(e))

        return None

    def _build_context_from_chunks(self, chunks: list[RetrievedChunk]) -> str:
        """Build context string from RAG chunks for LLM prompt.

        Args:
            chunks: Retrieved RAG chunks

        Returns:
            Combined context string (limited to prevent token overflow)
        """
        max_context_chars = 1500
        context_parts = []
        total_chars = 0

        for chunk in chunks[:3]:
            content = chunk.content[:500]
            if total_chars + len(content) > max_context_chars:
                break
            context_parts.append(f"- {content}")
            total_chars += len(content)

        return "\n".join(context_parts)

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
