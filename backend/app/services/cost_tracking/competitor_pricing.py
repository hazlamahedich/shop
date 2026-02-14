"""Competitor pricing estimation for cost comparison.

Provides ManyChat cost estimation based on message volume and contact tiers.
Used for cost comparison display to highlight shop's pay-per-token value.
"""

from __future__ import annotations

from decimal import Decimal

COMPETITOR_PRICING = {
    "manychat": {
        "name": "ManyChat",
        "tiers": [
            {"name": "Free", "contacts": 1000, "monthly": Decimal("0"), "messages_included": 0},
            {"name": "Pro", "contacts": 500, "monthly": Decimal("15"), "messages_included": 0},
            {
                "name": "Business",
                "contacts": 2500,
                "monthly": Decimal("25"),
                "messages_included": 0,
            },
            {
                "name": "Business+",
                "contacts": 10000,
                "monthly": Decimal("50"),
                "messages_included": 0,
            },
            {
                "name": "Business++",
                "contacts": 25000,
                "monthly": Decimal("99"),
                "messages_included": 0,
            },
        ],
        "message_cost": Decimal("0.015"),
        "notes": "ManyChat charges subscription + per-message overages",
    }
}


def estimate_manychat_cost(message_count: int) -> Decimal:
    """Estimate ManyChat monthly cost based on message volume.

    Uses conservative pricing (Pro tier minimum + message costs).

    Estimation Methodology:
    - Contact estimation: Assumes 10% message-to-contact ratio (10 messages ≈ 1 contact)
      This is conservative for typical chatbot usage patterns where one contact
      may generate multiple messages across a session.
    - Tier selection: Based on estimated contacts, selects appropriate subscription tier
    - Message costs: Assumes 50% of messages are billable beyond included allocation
      at average rate of $0.015/message

    Note: This is an ESTIMATE for comparison purposes only. Actual ManyChat costs
    depend on their current pricing, contact list size, and message tagging rules.

    Args:
        message_count: Number of messages sent in the billing period

    Returns:
        Estimated monthly cost in USD
    """
    if message_count <= 0:
        return Decimal("0")

    estimated_contacts = max(500, message_count // 10)

    if estimated_contacts <= 500:
        tier_cost = Decimal("15")
    elif estimated_contacts <= 2500:
        tier_cost = Decimal("25")
    elif estimated_contacts <= 10000:
        tier_cost = Decimal("50")
    else:
        tier_cost = Decimal("99")

    billable_messages = message_count // 2
    message_cost = Decimal("0.015") * billable_messages

    return tier_cost + message_cost


def get_comparison_methodology(message_count: int) -> str:
    """Generate methodology explanation for cost comparison.

    Args:
        message_count: Number of messages sent in the billing period

    Returns:
        Human-readable methodology string
    """
    return (
        f"ManyChat pricing: $15-99/month based on contacts + $0.01-0.02 per message. "
        f"Shop pricing: Pay only for LLM tokens used (typically $0.10-5.00/month for small businesses). "
        f"Comparison based on {message_count} messages this month."
    )


def calculate_savings(merchant_spend: Decimal, message_count: int) -> dict:
    """Calculate cost comparison and savings vs ManyChat.

    Args:
        merchant_spend: Merchant's actual spend in USD (must be non-negative)
        message_count: Number of messages sent in the billing period

    Returns:
        Dictionary with comparison data:
            - manyChatEstimate: Estimated ManyChat cost
            - savingsAmount: Amount saved with shop
            - savingsPercentage: Percentage saved (0-100)
            - merchantSpend: Actual shop spend
            - methodology: Explanation string

    Raises:
        ValueError: If merchant_spend is negative
    """
    merchant_spend = Decimal(str(merchant_spend))

    if merchant_spend < 0:
        raise ValueError("merchant_spend must be non-negative")

    many_chat_estimate = estimate_manychat_cost(message_count)

    if many_chat_estimate > 0:
        savings_amount = many_chat_estimate - merchant_spend
        savings_percentage = float((savings_amount / many_chat_estimate) * 100)
    else:
        savings_amount = Decimal("0")
        savings_percentage = 0.0

    return {
        "manyChatEstimate": float(many_chat_estimate),
        "savingsAmount": float(savings_amount),
        "savingsPercentage": savings_percentage,
        "merchantSpend": float(merchant_spend),
        "methodology": get_comparison_methodology(message_count),
    }


calculate_cost_comparison = calculate_savings
