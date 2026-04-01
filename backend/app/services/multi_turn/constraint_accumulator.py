"""Constraint accumulator for multi-turn query handling.

Story 11-2: Multi-Turn Query Handling (AC2, AC3, AC8)
Merges constraints across turns, detects duplicates and contradictions.
"""

from __future__ import annotations

import re
from typing import Any

import structlog

from app.core.errors import ErrorCode

logger = structlog.get_logger(__name__)

MAX_CONSTRAINTS = 20

CONTRADICTORY_KEYWORDS: dict[str, set[str]] = {
    "premium": {"budget", "cheap", "affordable", "under", "less"},
    "cheap": {"premium", "expensive", "luxury"},
    "luxury": {"budget", "cheap", "affordable"},
}

ECOMMERCE_CONSTRAINT_PATTERNS: dict[str, list[str]] = {
    "budget_max": [
        r"under\s+\$?(\d+)",
        r"less\s+than\s+\$?(\d+)",
        r"below\s+\$?(\d+)",
        r"max\s+\$?(\d+)",
    ],
    "budget_min": [
        r"over\s+\$?(\d+)",
        r"more\s+than\s+\$?(\d+)",
        r"above\s+\$?(\d+)",
        r"min\s+\$?(\d+)",
    ],
    "brand": [
        r"(?:brand|from|by|make)\s+(?:is\s+)?([a-z]+(?:\s+[a-z]+){0,2})",
        r"\b(nike|adidas|puma|reebok|under armour|new balance|asics|vans|converse|skechers|gucci|prada|chanel|versace|zara|h&m|uniqlo|levis|gap|tommy hilfiger|ralph lauren|north face|patagonia|columbia|lululemon|fila|jordan|yeezy|balenciaga)\b",
    ],
    "size": [r"size\s+(xs|s|m|l|xl|xxl|\d+)"],
    "color": [
        r"(?:color\s+)?(red|blue|green|black|white|yellow|purple|pink|orange|brown|grey|gray|beige|navy)"
    ],
    "category": [r"(shoes?|shirt|pants?|jacket|dress|hat|bag|watch|phone|laptop|headphones?)"],
    "product_type": [r"(running|casual|formal|sports?|outdoor|indoor|gym|training|walking)"],
}

GENERAL_CONSTRAINT_PATTERNS: dict[str, list[str]] = {
    "severity": [r"(urgent|critical|important|minor|low\s+priority|high\s+priority|asap)"],
    "timeframe": [
        r"(today|yesterday|last\s+week|this\s+week|right\s+now|just\s+now|recently|ongoing|constant)"
    ],
    "issue_type": [
        r"(login|payment|shipping|delivery|refund|return|cancel|account|password|error|bug|broken)"
    ],
}


class ConstraintAccumulator:
    """Accumulates and merges constraints across multi-turn conversations.

    Supports both e-commerce and general mode constraints.
    Detects duplicates, contradictions, and enforces max constraint count.
    """

    def __init__(self) -> None:
        self.logger = structlog.get_logger(__name__)

    def accumulate(
        self,
        message: str,
        existing_constraints: dict[str, Any],
        mode: str = "ecommerce",
    ) -> dict[str, Any]:
        new_constraints = self._extract_constraints(message, mode)

        if not new_constraints:
            return dict(existing_constraints)

        merged = dict(existing_constraints)

        for key, value in new_constraints.items():
            if key in merged and merged[key] == value:
                continue

            if self._detect_contradictory_constraints(key, value, merged):
                self.logger.warning(
                    "Constraint conflict detected",
                    error_code=7092,
                    constraint_key=key,
                    new_value=value,
                    existing_value=merged.get(key),
                    all_constraints=merged,
                )
                merged[f"{key}_conflict"] = {
                    "previous": merged.get(key),
                    "new": value,
                }
                merged[key] = value
            else:
                merged[key] = value

        merged = self._truncate_oldest_constraints(merged)

        return merged

    def _extract_constraints(self, message: str, mode: str) -> dict[str, Any]:
        constraints: dict[str, Any] = {}

        if mode == "ecommerce":
            patterns = ECOMMERCE_CONSTRAINT_PATTERNS
        else:
            patterns = GENERAL_CONSTRAINT_PATTERNS

        lower_msg = message.lower().strip()

        for constraint_name, patterns_list in patterns.items():
            for pattern in patterns_list:
                match = re.search(pattern, lower_msg)
                if match:
                    if constraint_name in ("budget_max", "budget_min"):
                        try:
                            constraints[constraint_name] = float(match.group(1))
                        except (ValueError, IndexError):
                            pass
                    elif match.lastindex and match.lastindex >= 1:
                        constraints[constraint_name] = match.group(1).strip()
                    else:
                        constraints[constraint_name] = match.group(0).strip()
                    break

        return constraints

    def _detect_contradictory_constraints(
        self,
        key: str,
        new_value: Any,
        existing: dict[str, Any],
    ) -> bool:
        if key in existing:
            old_value = existing[key]
            if old_value == new_value:
                return False

        if key == "budget_max" and "budget_min" in existing:
            if isinstance(new_value, (int, float)) and isinstance(
                existing["budget_min"], (int, float)
            ):
                if new_value < existing["budget_min"]:
                    return True

        if key == "budget_min" and "budget_max" in existing:
            if isinstance(new_value, (int, float)) and isinstance(
                existing["budget_max"], (int, float)
            ):
                if new_value > existing["budget_max"]:
                    return True

        if isinstance(new_value, str) and key in existing:
            new_lower = new_value.lower()
            old_value = existing[key]
            for keyword_set in CONTRADICTORY_KEYWORDS.values():
                if new_lower in keyword_set:
                    old_lower = str(old_value).lower()
                    for other_keyword in keyword_set:
                        if other_keyword != new_lower and old_lower == other_keyword:
                            return True

        return False

    def _truncate_oldest_constraints(
        self,
        constraints: dict[str, Any],
        max_count: int = MAX_CONSTRAINTS,
    ) -> dict[str, Any]:
        if len(constraints) <= max_count:
            return constraints

        self.logger.warning(
            "Constraint count exceeded max, truncating oldest",
            count=len(constraints),
            max=max_count,
        )

        priority_keys = {"budget_max", "budget_min", "category", "brand", "issue_type", "severity"}
        priority_items = {k: v for k, v in constraints.items() if k in priority_keys}
        other_items = {k: v for k, v in constraints.items() if k not in priority_keys}

        remaining_slots = max_count - len(priority_items)
        if remaining_slots > 0:
            for i, (k, v) in enumerate(other_items.items()):
                if i >= remaining_slots:
                    break
                priority_items[k] = v

        return priority_items

    def format_constraint_summary(
        self, constraints: dict[str, Any], mode: str = "ecommerce"
    ) -> str:
        if not constraints:
            return "No specific preferences yet."

        parts: list[str] = []
        clean = {k: v for k, v in constraints.items() if not k.endswith("_conflict")}

        if mode == "ecommerce":
            if "category" in clean:
                parts.append(clean["category"])
            if "product_type" in clean:
                parts.append(clean["product_type"])
            if "budget_max" in clean:
                parts.append(f"under ${clean['budget_max']}")
            if "budget_min" in clean:
                parts.append(f"over ${clean['budget_min']}")
            if "brand" in clean:
                parts.append(f"from {clean['brand'].title()}")
            if "size" in clean:
                parts.append(f"size {clean['size']}")
            if "color" in clean:
                parts.append(f"in {clean['color']}")
        else:
            if "issue_type" in clean:
                parts.append(f"issue type: {clean['issue_type']}")
            if "severity" in clean:
                parts.append(f"severity: {clean['severity']}")
            if "timeframe" in clean:
                parts.append(f"timeframe: {clean['timeframe']}")
            if "topic" in clean:
                parts.append(f"topic: {clean['topic']}")

        if not parts:
            return "No specific preferences yet."

        return ", ".join(parts)

    def detect_duplicate_constraints(
        self,
        new_constraints: dict[str, Any],
        existing_constraints: dict[str, Any],
    ) -> list[str]:
        duplicates = []
        for key, value in new_constraints.items():
            if key in existing_constraints and existing_constraints[key] == value:
                duplicates.append(key)
        return duplicates
