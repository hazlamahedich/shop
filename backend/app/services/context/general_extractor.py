"""General mode context extractor.

Story 11-1: Conversation Context Memory
Extracts general mode context: topics, documents, issues, escalation status.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.context.base import BaseContextExtractor


class GeneralContextExtractor(BaseContextExtractor):
    """Extract context for general mode conversations.

    Tracks:
    - Topics discussed
    - Documents referenced (KB articles, FAQs)
    - Support issues (login, billing, technical)
    - Escalation status
    """

    # Common support topics
    SUPPORT_TOPICS = [
        "login",
        "password",
        "account",
        "sign in",
        "authentication",
        "billing",
        "payment",
        "refund",
        "charge",
        "invoice",
        "shipping",
        "delivery",
        "tracking",
        "order",
        "technical",
        "error",
        "bug",
        "crash",
        "slow",
        "feature",
        "request",
        "enhancement",
    ]

    # Issue type mapping
    ISSUE_KEYWORDS = {
        "login": ["login", "password", "sign in", "auth", "account access"],
        "billing": ["billing", "payment", "charge", "refund", "invoice"],
        "technical": ["error", "bug", "crash", "slow", "broken", "not working"],
        "shipping": ["shipping", "delivery", "tracking", "package"],
        "feature": ["feature", "request", "enhancement", "suggestion"],
    }

    async def extract(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Extract general mode context from user message.

        Args:
            message: User message to analyze
            context: Current conversation context

        Returns:
            Updated context with extracted information
        """
        updates = {}
        message_lower = message.lower()

        # Extract topics discussed
        topics = self._extract_topics(message)
        if topics:
            updates["topics_discussed"] = topics

        # Extract document references
        documents = self._extract_document_references(message)
        if documents:
            updates["documents_referenced"] = documents

        # Detect and classify support issues
        issues = self._detect_support_issues(message, context)
        if issues:
            updates["support_issues"] = issues

        # Check escalation keywords
        escalation = self._check_escalation(message_lower)
        if escalation:
            updates["escalation_status"] = escalation

        # Increment turn count
        updates["turn_count"] = context.get("turn_count", 0) + 1

        return updates

    def _extract_topics(self, message: str) -> list[str] | None:
        """Extract topics discussed in message.

        Args:
            message: User message

        Returns:
            List of topics or None
        """
        message_lower = message.lower()
        topics_found = []

        for topic in self.SUPPORT_TOPICS:
            if re.search(rf"\b{re.escape(topic)}\b", message_lower):
                topics_found.append(topic)

        return topics_found if topics_found else None

    def _extract_document_references(self, message: str) -> list[int] | None:
        """Extract document/KB article references from message.

        Looks for patterns like "KB-123", "article-456", etc.

        Args:
            message: User message

        Returns:
            List of document IDs or None
        """
        # Pattern: KB-123, article-456, doc-789
        pattern = r"(?:kb|article|doc|faq)[\s\-]+(\d+)"
        matches = re.findall(pattern, message, re.IGNORECASE)

        if matches:
            return [int(match) for match in matches]
        return None

    def _detect_support_issues(
        self, message: str, context: dict[str, Any]
    ) -> list[dict[str, Any]] | None:
        """Detect and classify support issues.

        Args:
            message: User message
            context: Current conversation context

        Returns:
            List of issues with type and status, or None
        """
        message_lower = message.lower()
        issues = []

        for issue_type, keywords in self.ISSUE_KEYWORDS.items():
            if any(re.search(rf"\b{re.escape(kw)}\b", message_lower) for kw in keywords):
                # Check if this issue type already exists
                existing_issues = context.get("support_issues", [])
                existing_types = {issue.get("type") for issue in existing_issues}

                if issue_type not in existing_types:
                    issues.append(
                        {
                            "type": issue_type,
                            "status": "pending",
                            "message": message[:100],  # Truncate for storage
                        }
                    )

        return issues if issues else None

    def _check_escalation(self, message_lower: str) -> str | None:
        """Check if message contains escalation keywords.

        Args:
            message_lower: Lowercase message

        Returns:
            Escalation level or None
        """
        high_patterns = [
            r"\bspeak to (a )?human\b",
            r"\btalk to (a )?(human|person)\b",
            r"\bsupervisor\b",
            r"\bmanager\b",
            r"\burgent\b",
        ]
        if any(re.search(p, message_lower) for p in high_patterns):
            return "high"

        medium_patterns = [
            r"\bfrustrated\b",
            r"\bangry\b",
            r"\bupset\b",
            r"\bnot happy\b",
            r"\bdisappointed\b",
        ]
        if any(re.search(p, message_lower) for p in medium_patterns):
            return "medium"

        low_patterns = [
            r"\bconfused\b",
            r"\bdon'?t understand\b",
            r"\bhelp\b",
            r"\bsupport\b",
        ]
        if any(re.search(p, message_lower) for p in low_patterns):
            return "low"

        return None
