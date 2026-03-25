"""Query rewriter for contextualizing follow-up questions.

Rewrites vague follow-up questions into standalone queries using
conversation history for better RAG retrieval.

Story 10-1: Contextual RAG for follow-up questions
"""

from __future__ import annotations

import structlog

from app.services.llm.base_llm_service import LLMMessage

logger = structlog.get_logger(__name__)

REWRITE_SYSTEM_PROMPT = """You are a query rewriter. Your task is to rewrite follow-up questions into standalone queries that can be understood without conversation context.

Rules:
1. If the question is already standalone, return it unchanged
2. If the question refers to previous context (using pronouns like "he", "she", "it", "they", or vague references like "what about X"), rewrite it to include the relevant context
3. Keep the rewritten query concise and focused on the key information needed
4. Do not add information not present in the conversation history

Examples:
- History: "Where did John graduate?" Answer: "John graduated from MIT"
  Query: "What about his major?"
  Rewrite: "What was John's major at MIT?"

- History: "Tell me about the product warranty"
  Query: "How long is it?"
  Rewrite: "How long is the product warranty?"

- History: "Sherwin graduated from Ateneo de Manila University with B.S. Management in Information Systems in March 2002"
  Query: "What about March?"
  Rewrite: "What is significant about March 2002 in Sherwin's education?"

Return ONLY the rewritten query, nothing else."""


class QueryRewriter:
    """Rewrites follow-up questions into standalone queries.

    Uses LLM to expand vague follow-up questions using conversation history.
    This improves RAG retrieval for contextual queries.
    """

    def __init__(self, llm_service):
        """Initialize query rewriter.

        Args:
            llm_service: LLM service for query rewriting
        """
        self.llm_service = llm_service

    async def rewrite_query(
        self,
        query: str,
        conversation_history: list[dict],
    ) -> str:
        """Rewrite a follow-up question into a standalone query.

        Args:
            query: Current user query
            conversation_history: Recent conversation messages

        Returns:
            Rewritten standalone query, or original if rewriting fails
        """
        if not conversation_history:
            return query

        try:
            messages = [
                LLMMessage(role="system", content=REWRITE_SYSTEM_PROMPT),
            ]

            history_text = self._format_history(conversation_history[-4:])
            messages.append(
                LLMMessage(
                    role="user",
                    content=f"Conversation history:\n{history_text}\n\nQuery: {query}\n\nRewrite:",
                )
            )

            response = await self.llm_service.chat(
                messages=messages,
                temperature=0.1,
            )

            rewritten = response.content.strip()

            if rewritten and len(rewritten) > len(query) * 0.5:
                logger.info(
                    "query_rewritten",
                    original=query[:50],
                    rewritten=rewritten[:50],
                )
                return rewritten

            return query

        except Exception as e:
            logger.warning(
                "query_rewrite_failed",
                error=str(e),
                fallback_to_original=True,
            )
            return query

    def _format_history(self, history: list[dict]) -> str:
        """Format conversation history for LLM prompt.

        Args:
            history: List of message dicts with 'role' and 'content'

        Returns:
            Formatted history string
        """
        parts = []
        for msg in history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")[:200]
            parts.append(f"{role}: {content}")

        return "\n".join(parts)

    def is_follow_up(self, query: str) -> bool:
        """Detect if a query is likely a follow-up question.

        Args:
            query: User query to analyze

        Returns:
            True if query appears to be a follow-up
        """
        query_lower = query.lower().strip()

        follow_up_patterns = [
            "what about",
            "how about",
            "and the",
            "tell me more",
            "can you explain",
            "what else",
            "who is",
            "when did",
            "where is",
            "why did",
            "how did",
            "what is",
        ]

        pronouns = [" he ", " she ", " it ", " they ", " them ", " his ", " her ", " its "]

        for pattern in follow_up_patterns:
            if query_lower.startswith(pattern):
                return True

        for pronoun in pronouns:
            if pronoun in f" {query_lower} ":
                return True

        if len(query_lower.split()) <= 4:
            return True

        return False
