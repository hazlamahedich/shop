"""LLM Cost Tracking service.

Tracks token usage and costs per conversation for budget management
and cost transparency. Supports cost estimation and real-time tracking.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.llm_conversation_cost import LLMConversationCost
from app.services.export.cost_calculator import CostCalculator
from app.services.llm.base_llm_service import LLMResponse
from app.services.cost_tracking.pricing import LLM_PRICING


logger = structlog.get_logger(__name__)


class CostTrackingService:
    """Service for tracking LLM costs per conversation.

    Provides:
    - Cost record creation and persistence
    - Conversation cost aggregation and retrieval
    - Cost summary with date filtering
    - Daily breakdown generation
    - Merchant isolation enforcement
    """

    def __init__(self) -> None:
        """Initialize cost tracking service."""
        self.cost_calculator = CostCalculator()

    async def create_cost_record(
        self,
        db: AsyncSession,
        conversation_id: str,
        merchant_id: int,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        input_cost_usd: float,
        output_cost_usd: float,
        total_cost_usd: float,
        processing_time_ms: Optional[float] = None,
    ) -> LLMConversationCost:
        """Create a new LLM cost record.

        Args:
            db: Database session
            conversation_id: Conversation identifier
            merchant_id: Merchant ID for isolation
            provider: LLM provider name (e.g., "openai", "ollama")
            model: Model name (e.g., "gpt-4o-mini")
            prompt_tokens: Input token count
            completion_tokens: Output token count
            total_tokens: Total token count
            input_cost_usd: Input cost in USD
            output_cost_usd: Output cost in USD
            total_cost_usd: Total cost in USD
            processing_time_ms: Request processing time in milliseconds

        Returns:
            Created LLMConversationCost record

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        if not conversation_id:
            raise ValueError("conversation_id is required")
        if not merchant_id:
            raise ValueError("merchant_id is required")
        if not provider:
            raise ValueError("provider is required")
        if not model:
            raise ValueError("model is required")
        if prompt_tokens < 0 or completion_tokens < 0 or total_tokens < 0:
            raise ValueError("token counts must be non-negative")
        if total_cost_usd < 0:
            raise ValueError("total_cost_usd must be non-negative")

        # Create cost record
        cost_record = LLMConversationCost(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            input_cost_usd=input_cost_usd,
            output_cost_usd=output_cost_usd,
            total_cost_usd=total_cost_usd,
            request_timestamp=datetime.utcnow(),
            processing_time_ms=processing_time_ms,
        )

        db.add(cost_record)
        await db.flush()

        logger.info(
            "cost_record_created",
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            provider=provider,
            model=model,
            total_cost_usd=total_cost_usd,
            total_tokens=total_tokens,
        )

        return cost_record

    async def get_conversation_costs(
        self,
        db: AsyncSession,
        merchant_id: int,
        conversation_id: str,
    ) -> dict:
        """Get aggregated cost data for a specific conversation.

        Args:
            db: Database session
            merchant_id: Merchant ID for isolation
            conversation_id: Conversation identifier

        Returns:
            Dictionary with aggregated cost data:
                - conversationId: Conversation ID
                - totalCostUsd: Total cost in USD
                - totalTokens: Total tokens used
                - requestCount: Number of LLM requests
                - avgCostPerRequest: Average cost per request
                - provider: Primary provider used
                - model: Primary model used
                - requests: List of individual cost records

        Raises:
            ValueError: If conversation has no cost data
        """
        # Enforce merchant isolation
        query = (
            select(LLMConversationCost)
            .where(
                and_(
                    LLMConversationCost.conversation_id == conversation_id,
                    LLMConversationCost.merchant_id == merchant_id,
                )
            )
            .order_by(desc(LLMConversationCost.request_timestamp))
        )

        result = await db.execute(query)
        cost_records = result.scalars().all()

        if not cost_records:
            raise ValueError(f"No cost data found for conversation: {conversation_id}")

        # Aggregate data
        total_cost_usd = sum(r.total_cost_usd for r in cost_records)
        total_tokens = sum(r.total_tokens for r in cost_records)
        request_count = len(cost_records)
        avg_cost_per_request = total_cost_usd / request_count if request_count > 0 else 0

        # Get primary provider/model (most recent)
        primary_record = cost_records[0] if cost_records else None
        provider = primary_record.provider if primary_record else "unknown"
        model = primary_record.model if primary_record else "unknown"

        # Format request breakdown
        requests = [
            {
                "id": r.id,
                "requestTimestamp": r.request_timestamp.isoformat(),
                "provider": r.provider,
                "model": r.model,
                "promptTokens": r.prompt_tokens,
                "completionTokens": r.completion_tokens,
                "totalTokens": r.total_tokens,
                "inputCostUsd": r.input_cost_usd,
                "outputCostUsd": r.output_cost_usd,
                "totalCostUsd": r.total_cost_usd,
                "processingTimeMs": r.processing_time_ms,
            }
            for r in cost_records
        ]

        return {
            "conversationId": conversation_id,
            "totalCostUsd": round(total_cost_usd, 4),
            "totalTokens": total_tokens,
            "requestCount": request_count,
            "avgCostPerRequest": round(avg_cost_per_request, 4),
            "provider": provider,
            "model": model,
            "requests": requests,
        }

    async def get_cost_summary(
        self,
        db: AsyncSession,
        merchant_id: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict:
        """Get aggregated cost summary with trend analysis.

        Calculates current period summary and previous equivalent period
        summary to enable percentage change comparisons (trends).
        """
        # 1. Determine date ranges
        now = datetime.utcnow()
        if date_from:
            current_from = datetime.fromisoformat(date_from)
        else:
            current_from = now - timedelta(days=30)

        if date_to:
            current_to = datetime.fromisoformat(date_to).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        else:
            current_to = now

        # Calculate previous period range
        duration = current_to - current_from
        prev_to = current_from - timedelta(microseconds=1)
        prev_from = prev_to - duration

        # 2. Get summaries for both periods
        current_summary = await self._calculate_period_summary(
            db, merchant_id, current_from, current_to
        )
        previous_summary = await self._calculate_period_summary(db, merchant_id, prev_from, prev_to)

        # 3. Generate daily breakdown (only for current period)
        daily_breakdown = await self._calculate_daily_costs(db, merchant_id, date_from, date_to)

        # 4. Merge and return
        return {
            **current_summary,
            "dailyBreakdown": daily_breakdown,
            "previousPeriodSummary": previous_summary,
        }

    async def _calculate_period_summary(
        self,
        db: AsyncSession,
        merchant_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Helper to calculate summary for a specific date range."""
        query = select(LLMConversationCost).where(
            and_(
                LLMConversationCost.merchant_id == merchant_id,
                LLMConversationCost.request_timestamp >= start_date,
                LLMConversationCost.request_timestamp <= end_date,
            )
        )

        result = await db.execute(query)
        cost_records = result.scalars().all()

        if not cost_records:
            return {
                "totalCostUsd": 0.0,
                "totalTokens": 0,
                "requestCount": 0,
                "avgCostPerRequest": 0.0,
                "topConversations": [],
                "costsByProvider": {},
            }

        # Calculate totals
        total_cost_usd = sum(r.total_cost_usd for r in cost_records)
        total_tokens = sum(r.total_tokens for r in cost_records)
        request_count = len(cost_records)
        avg_cost_per_request = total_cost_usd / request_count if request_count > 0 else 0

        # Get top conversations
        conversation_costs = {}
        for record in cost_records:
            conv_id = record.conversation_id
            if conv_id not in conversation_costs:
                conversation_costs[conv_id] = {"totalCostUsd": 0.0, "requestCount": 0}
            conversation_costs[conv_id]["totalCostUsd"] += record.total_cost_usd
            conversation_costs[conv_id]["requestCount"] += 1

        top_conversations = sorted(
            [{"conversationId": k, **v} for k, v in conversation_costs.items()],
            key=lambda x: x["totalCostUsd"],
            reverse=True,
        )[:10]

        # Group by provider
        costs_by_provider = {}
        for record in cost_records:
            provider = record.provider
            if provider not in costs_by_provider:
                costs_by_provider[provider] = {"costUsd": 0.0, "requests": 0}
            costs_by_provider[provider]["costUsd"] += record.total_cost_usd
            costs_by_provider[provider]["requests"] += 1

        # Round values
        for provider in costs_by_provider:
            costs_by_provider[provider]["costUsd"] = round(
                costs_by_provider[provider]["costUsd"], 4
            )

        return {
            "totalCostUsd": round(total_cost_usd, 4),
            "totalTokens": total_tokens,
            "requestCount": request_count,
            "avgCostPerRequest": round(avg_cost_per_request, 4),
            "topConversations": top_conversations,
            "costsByProvider": costs_by_provider,
        }

    async def _calculate_daily_costs(
        self,
        db: AsyncSession,
        merchant_id: int,
        date_from: Optional[str],
        date_to: Optional[str],
    ) -> list[dict]:
        """Calculate daily cost breakdown.

        Args:
            db: Database session
            merchant_id: Merchant ID for isolation
            date_from: Start date filter (ISO 8601 string)
            date_to: End date filter (ISO 8601 string)

        Returns:
            List of daily cost summaries
        """
        # Build query with date grouping
        query = select(
            func.date(LLMConversationCost.request_timestamp).label("date"),
            func.sum(LLMConversationCost.total_cost_usd).label("totalCostUsd"),
            func.count(LLMConversationCost.id).label("requestCount"),
        ).where(LLMConversationCost.merchant_id == merchant_id)

        # Apply date filters
        if date_from:
            try:
                from_datetime = datetime.fromisoformat(date_from)
                query = query.where(LLMConversationCost.request_timestamp >= from_datetime)
            except ValueError:
                pass

        if date_to:
            try:
                to_datetime = datetime.fromisoformat(date_to)
                to_datetime = to_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
                query = query.where(LLMConversationCost.request_timestamp <= to_datetime)
            except ValueError:
                pass

        query = query.group_by(func.date(LLMConversationCost.request_timestamp))
        query = query.order_by(func.date(LLMConversationCost.request_timestamp))

        result = await db.execute(query)
        daily_rows = result.all()

        return [
            {
                "date": str(row.date),
                "totalCostUsd": round(float(row.totalCostUsd or 0), 4),
                "requestCount": row.requestCount or 0,
            }
            for row in daily_rows
        ]


# Standalone helper function for automatic LLM request tracking
async def track_llm_request(
    db: AsyncSession,
    llm_response: LLMResponse,
    conversation_id: str,
    merchant_id: int,
    processing_time_ms: Optional[float] = None,
) -> Optional[LLMConversationCost]:
    """Track an LLM request automatically after receiving a response.

    This helper function extracts token and cost information from an LLMResponse
    and creates a cost record. It should be called after each LLM request.

    Args:
        db: Database session
        llm_response: The LLM response object containing token usage metadata
        conversation_id: Conversation identifier (platform_sender_id)
        merchant_id: Merchant ID for isolation
        processing_time_ms: Request processing time in milliseconds (optional)

    Returns:
        Created cost record, or None if tracking is disabled (e.g., Ollama)

    Example:
        response = await llm_service.chat(messages)
        await track_llm_request(db, response, conversation_id="user123", merchant_id=1)

    Note:
        - Ollama requests are tracked with $0.00 cost (local hosting)
        - Token counts are extracted from response metadata
        - Costs are calculated using provider pricing tables
    """
    try:
        # Extract token counts from metadata
        metadata = llm_response.metadata or {}
        input_tokens = metadata.get("input_tokens", 0)
        output_tokens = metadata.get("output_tokens", metadata.get("completion_tokens", 0))
        total_tokens = llm_response.tokens_used

        # If not in metadata, estimate from total (50/50 split assumption)
        if not input_tokens and not output_tokens and total_tokens:
            input_tokens = total_tokens // 2
            output_tokens = total_tokens - input_tokens

        # Calculate costs using provider pricing tables
        # Each provider has different input/output token pricing
        provider = llm_response.provider
        model = llm_response.model

        # Get pricing for provider/model (with fallbacks)
        # LLM_PRICING is imported from pricing.py for centralized configuration
        if provider in LLM_PRICING:
            provider_pricing = LLM_PRICING[provider]
            if isinstance(provider_pricing, dict) and model in provider_pricing:
                pricing = provider_pricing[model]
            elif isinstance(provider_pricing, dict) and "input" in provider_pricing:
                pricing = provider_pricing  # Direct pricing dict
            else:
                # Fallback to Ollama (free)
                pricing = LLM_PRICING["ollama"]
        else:
            # Unknown provider, treat as free
            pricing = LLM_PRICING["ollama"]

        # Calculate input and output costs
        input_cost_usd = (input_tokens / 1_000_000) * pricing.get("input", 0.0)
        output_cost_usd = (output_tokens / 1_000_000) * pricing.get("output", 0.0)
        total_cost_usd = input_cost_usd + output_cost_usd

        # Create cost record
        service = CostTrackingService()
        cost_record = await service.create_cost_record(
            db=db,
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            provider=provider,
            model=model,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=total_tokens,
            input_cost_usd=input_cost_usd,
            output_cost_usd=output_cost_usd,
            total_cost_usd=total_cost_usd,
            processing_time_ms=processing_time_ms,
        )

        logger.info(
            "llm_request_tracked",
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            provider=provider,
            model=model,
            total_cost_usd=total_cost_usd,
            total_tokens=total_tokens,
        )

        return cost_record

    except Exception as e:
        # Log error but don't fail the request
        logger.error(
            "llm_request_tracking_failed",
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            error=str(e),
        )
        return None
