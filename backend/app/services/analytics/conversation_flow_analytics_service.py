from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy import asc, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.conversation_context import ConversationTurn

logger = structlog.get_logger(__name__)


class ConversationFlowAnalyticsService:
    """Analytics service for conversation flow insights.

    Reads from conversation_turns table (populated by Story 11.12a) to provide:
    - Conversation length distribution (AC1)
    - Clarification pattern analysis (AC2)
    - Friction point detection (AC3)
    - Sentiment distribution by stage (AC4)
    - Human handoff correlation (AC5)
    - Context utilization metrics (AC6)

    Error codes: 7120-7126 (7127 reserved for 11.12a turn write errors)
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _get_turns_base_query(self, merchant_id: int, days: int) -> Any:
        """Shared base query: conversation_turns JOIN conversations, filtered by merchant and date."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return (
            select(ConversationTurn)
            .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
            .where(Conversation.merchant_id == merchant_id)
            .where(ConversationTurn.created_at >= cutoff)
        )

    async def get_overview(self, merchant_id: int, days: int = 30) -> dict[str, Any]:
        """Overview: Aggregated summary combining key metrics from all sub-analyses."""
        try:
            length_data = await self.get_conversation_length_distribution(merchant_id, days)
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            total_result = await self.db.execute(
                select(func.count(func.distinct(Conversation.id)))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.created_at >= cutoff)
            )
            total_conversations = total_result.scalar() or 0

            if total_conversations == 0 and not length_data.get("has_data"):
                return {
                    "has_data": False,
                    "message": "No conversation data available for this period.",
                }

            overview: dict[str, Any] = {
                "has_data": True,
                "data": {
                    "total_conversations": total_conversations,
                    "average_turns": length_data.get("data", {}).get("avg_turns", 0),
                    "completion_rate": None,
                    "by_mode": length_data.get("data", {}).get("by_mode", []),
                    "daily_trend": length_data.get("data", {}).get("daily_trend", []),
                },
                "period_days": days,
            }
            return overview

        except Exception as e:
            logger.error(
                "conversation_flow_overview_failed",
                merchant_id=merchant_id,
                days=days,
                error=str(e),
                error_code=7120,
            )
            return {
                "has_data": False,
                "message": "Unable to compute conversation flow overview.",
            }

    async def get_conversation_length_distribution(
        self, merchant_id: int, days: int = 30
    ) -> dict[str, Any]:
        """AC1: Conversation length distribution — avg/median/P90, grouped by mode, daily trend."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            mode_expr = ConversationTurn.context_snapshot["mode"].astext
            conv_turn_counts = (
                select(
                    ConversationTurn.conversation_id,
                    Conversation.handoff_status,
                    mode_expr.label("mode"),
                    func.count(ConversationTurn.id).label("turn_count"),
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
                .group_by(
                    ConversationTurn.conversation_id,
                    Conversation.handoff_status,
                    mode_expr,
                )
                .subquery()
            )

            avg_turns_result = await self.db.execute(
                select(func.avg(conv_turn_counts.c.turn_count))
            )
            avg_turns = avg_turns_result.scalar()

            total_result = await self.db.execute(
                select(func.count(conv_turn_counts.c.conversation_id))
            )
            total_conversations = total_result.scalar() or 0

            if total_conversations == 0:
                return {
                    "has_data": False,
                    "message": "No conversation data available for this period.",
                }

            p90_result = await self.db.execute(
                select(func.percentile_cont(0.9).within_group(asc(conv_turn_counts.c.turn_count)))
            )
            p90_turns = p90_result.scalar()

            count_series = await self.db.execute(
                select(
                    conv_turn_counts.c.turn_count,
                    func.count(conv_turn_counts.c.conversation_id).label("conv_count"),
                ).group_by(conv_turn_counts.c.turn_count)
            )
            length_distribution = [
                {"turn_count": row.turn_count, "conversation_count": row.conv_count}
                for row in count_series
            ]

            mode_result = await self.db.execute(
                select(
                    conv_turn_counts.c.mode,
                    func.avg(conv_turn_counts.c.turn_count).label("avg_turns"),
                    func.count(conv_turn_counts.c.conversation_id).label("conv_count"),
                )
                .where(conv_turn_counts.c.mode != None)  # noqa: E711
                .group_by(conv_turn_counts.c.mode)
            )
            by_mode = [
                {
                    "mode": row.mode,
                    "avg_turns": round(float(row.avg_turns), 1) if row.avg_turns else 0,
                    "conversation_count": row.conv_count,
                }
                for row in mode_result
            ]

            day_trunc = func.date_trunc("day", ConversationTurn.created_at)
            daily_result = await self.db.execute(
                select(
                    day_trunc.label("day"),
                    func.count(ConversationTurn.id).label("total_turns"),
                    func.count(func.distinct(ConversationTurn.conversation_id)).label(
                        "total_conversations"
                    ),
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
                .group_by(day_trunc)
                .order_by(day_trunc)
            )
            daily_trend = [
                {
                    "date": row.day.strftime("%Y-%m-%d") if row.day else None,
                    "total_turns": row.total_turns,
                    "total_conversations": row.total_conversations,
                    "avg_turns": round(row.total_turns / row.total_conversations, 1)
                    if row.total_conversations > 0
                    else 0,
                }
                for row in daily_result
            ]

            sorted_counts = sorted(
                [row["turn_count"] for row in length_distribution],
            )
            median_turns = 0.0
            if sorted_counts:
                n = len(sorted_counts)
                if n % 2 == 0:
                    median_turns = round((sorted_counts[n // 2 - 1] + sorted_counts[n // 2]) / 2, 1)
                else:
                    median_turns = float(sorted_counts[n // 2])

            return {
                "has_data": True,
                "data": {
                    "avg_turns": round(float(avg_turns), 1) if avg_turns else 0,
                    "median_turns": median_turns,
                    "p90_turns": round(float(p90_turns), 1) if p90_turns else 0,
                    "total_conversations": total_conversations,
                    "length_distribution": length_distribution,
                    "by_mode": by_mode,
                    "daily_trend": daily_trend,
                },
                "period_days": days,
            }

        except Exception as e:
            logger.error(
                "conversation_length_distribution_failed",
                merchant_id=merchant_id,
                days=days,
                error=str(e),
                error_code=7121,
            )
            return {
                "has_data": False,
                "message": "Unable to compute conversation length distribution.",
            }

    async def get_clarification_patterns(self, merchant_id: int, days: int = 30) -> dict[str, Any]:
        """AC2: Most common clarification sequences, depth, success rate."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            clarifying_turns = (
                select(ConversationTurn)
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
                .where(ConversationTurn.context_snapshot["clarification_state"].astext != "IDLE")
            )
            result = await self.db.execute(clarifying_turns)
            turns = result.scalars().all()

            if not turns:
                return {
                    "has_data": False,
                    "message": "No clarification patterns found in this period.",
                }

            intent_chains: dict[str, list[str]] = defaultdict(list)
            conv_turns: dict[int, list[Any]] = defaultdict(list)

            for turn in turns:
                conv_turns[turn.conversation_id].append(turn)
                if turn.intent_detected:
                    intent_chains[turn.conversation_id].append(turn.intent_detected)

            sequences: dict[str, int] = defaultdict(int)
            for conv_id, intents in intent_chains.items():
                if len(intents) >= 2:
                    for i in range(len(intents) - 1):
                        seq = f"{intents[i]} -> {intents[i + 1]}"
                        sequences[seq] += 1

            top_sequences = sorted(sequences.items(), key=lambda x: x[1], reverse=True)[:5]

            total_depth = 0
            completed_count = 0
            total_clarifying = 0
            for conv_id, cturns in conv_turns.items():
                total_clarifying += 1
                attempt_counts = [
                    (
                        t.context_snapshot.get("clarification_attempt_count", 0)
                        if t.context_snapshot
                        else 0
                    )
                    for t in cturns
                ]
                max_depth = max(attempt_counts) if attempt_counts else 0
                total_depth += max_depth

                has_complete = any(
                    (
                        t.context_snapshot.get("clarification_state") == "COMPLETE"
                        if t.context_snapshot
                        else False
                    )
                    for t in cturns
                )
                if has_complete:
                    completed_count += 1

            avg_depth = round(total_depth / total_clarifying, 1) if total_clarifying > 0 else 0
            success_rate = (
                round(completed_count / total_clarifying * 100, 1) if total_clarifying > 0 else 0
            )

            return {
                "has_data": True,
                "data": {
                    "top_sequences": [
                        {"sequence": seq, "count": cnt} for seq, cnt in top_sequences
                    ],
                    "avg_clarification_depth": avg_depth,
                    "clarification_success_rate": success_rate,
                    "total_clarifying_conversations": total_clarifying,
                },
                "period_days": days,
            }

        except Exception as e:
            logger.error(
                "clarification_patterns_failed",
                merchant_id=merchant_id,
                days=days,
                error=str(e),
                error_code=7122,
            )
            return {
                "has_data": False,
                "message": "Unable to compute clarification patterns.",
            }

    async def get_friction_points(self, merchant_id: int, days: int = 30) -> dict[str, Any]:
        """AC3: Friction points — drop-off intents, repeated intents, processing time outliers."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            base_query = self._get_turns_base_query(merchant_id, days)
            result = await self.db.execute(base_query)
            all_turns = result.scalars().all()

            if not all_turns:
                return {
                    "has_data": False,
                    "message": "No significant friction points detected.",
                }

            conv_turns: dict[int, list[Any]] = defaultdict(list)
            for turn in all_turns:
                conv_turns[turn.conversation_id].append(turn)

            closed_conv_ids_result = await self.db.execute(
                select(Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.status == "closed")
                .where(Conversation.id.in_([t.conversation_id for t in all_turns]))
            )
            closed_conv_ids: set[int] = {row[0] for row in closed_conv_ids_result.all()}

            drop_off_intents: dict[str, int] = defaultdict(int)
            repeated_intents: dict[str, int] = defaultdict(int)
            processing_times: list[int] = []

            for conv_id, turns in conv_turns.items():
                sorted_turns = sorted(turns, key=lambda t: t.turn_number)
                for turn in sorted_turns:
                    snapshot = turn.context_snapshot or {}
                    pt = snapshot.get("processing_time_ms")
                    if pt is not None:
                        processing_times.append(pt)

                if conv_id in closed_conv_ids and sorted_turns:
                    last_intent = sorted_turns[-1].intent_detected
                    if last_intent:
                        drop_off_intents[last_intent] += 1

                for i in range(1, len(sorted_turns)):
                    if (
                        sorted_turns[i].intent_detected
                        and sorted_turns[i].intent_detected == sorted_turns[i - 1].intent_detected
                    ):
                        repeated_intents[sorted_turns[i].intent_detected] += 1

            sorted_drop_offs = sorted(drop_off_intents.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
            sorted_repeated = sorted(repeated_intents.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]

            p90_threshold = 0
            slow_turns_count = 0
            if processing_times:
                sorted_times = sorted(processing_times)
                idx = int(len(sorted_times) * 0.9)
                p90_threshold = sorted_times[min(idx, len(sorted_times) - 1)]
                slow_turns_count = sum(1 for t in processing_times if t > p90_threshold)

            friction_points = []
            for intent, count in sorted_drop_offs:
                friction_points.append(
                    {
                        "type": "drop_off",
                        "intent": intent,
                        "frequency": count,
                    }
                )
            for intent, count in sorted_repeated:
                friction_points.append(
                    {
                        "type": "repeated_intent",
                        "intent": intent,
                        "frequency": count,
                    }
                )
            friction_points.sort(key=lambda x: x["frequency"], reverse=True)

            return {
                "has_data": True,
                "data": {
                    "friction_points": friction_points[:10],
                    "drop_off_intents": [{"intent": i, "count": c} for i, c in sorted_drop_offs],
                    "repeated_intents": [{"intent": i, "count": c} for i, c in sorted_repeated],
                    "processing_time_p90_ms": p90_threshold,
                    "slow_turns_count": slow_turns_count,
                    "total_conversations_analyzed": len(conv_turns),
                },
                "period_days": days,
            }

        except Exception as e:
            logger.error(
                "friction_points_failed",
                merchant_id=merchant_id,
                days=days,
                error=str(e),
                error_code=7123,
            )
            return {
                "has_data": False,
                "message": "Unable to compute friction points.",
            }

    async def get_sentiment_distribution_by_stage(
        self, merchant_id: int, days: int = 30
    ) -> dict[str, Any]:
        """AC4: Sentiment distribution across early/mid/late conversation stages."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            stage_expr = case(
                (ConversationTurn.turn_number <= 3, "early"),
                (ConversationTurn.turn_number <= 7, "mid"),
                else_="late",
            )
            stmt = (
                select(
                    ConversationTurn.sentiment,
                    stage_expr.label("stage"),
                    func.count(ConversationTurn.id).label("count"),
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
                .where(ConversationTurn.sentiment != None)  # noqa: E711
                .group_by(ConversationTurn.sentiment, stage_expr)
            )
            result = await self.db.execute(stmt)
            rows = result.all()

            if not rows:
                return {
                    "has_data": False,
                    "message": "No sentiment data available for this period.",
                }

            stages: dict[str, dict[str, int]] = {
                "early": {},
                "mid": {},
                "late": {},
            }
            for row in rows:
                stage = row.stage
                sentiment = row.sentiment or "unknown"
                stages[stage][sentiment] = row.count

            negative_shift_result = await self.db.execute(
                select(
                    ConversationTurn.conversation_id,
                    ConversationTurn.sentiment,
                    ConversationTurn.turn_number,
                    ConversationTurn.intent_detected,
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
                .where(ConversationTurn.sentiment != None)  # noqa: E711
                .order_by(ConversationTurn.conversation_id, ConversationTurn.turn_number)
            )
            all_sentiment_turns = negative_shift_result.all()

            negative_shifts: list[dict[str, Any]] = []
            conv_sentiments: dict[int, list[Any]] = {}
            for turn in all_sentiment_turns:
                if turn.conversation_id not in conv_sentiments:
                    conv_sentiments[turn.conversation_id] = [turn]
                else:
                    conv_sentiments[turn.conversation_id].append(turn)

            for conv_id, turns in conv_sentiments.items():
                early_turns = [t for t in turns if t.turn_number <= 3]
                late_turns = [t for t in turns if t.turn_number >= 8]
                if early_turns and late_turns:
                    early_neg = sum(1 for t in early_turns if t.sentiment == "NEGATIVE") / len(
                        early_turns
                    )
                    late_neg = sum(1 for t in late_turns if t.sentiment == "NEGATIVE") / len(
                        late_turns
                    )
                    if late_neg > early_neg:
                        shift_intent = late_turns[0].intent_detected or "unknown"
                        negative_shifts.append(
                            {
                                "conversation_id": conv_id,
                                "early_negative_rate": round(early_neg, 2),
                                "late_negative_rate": round(late_neg, 2),
                                "intent_at_shift": shift_intent,
                            }
                        )

            return {
                "has_data": True,
                "data": {
                    "stages": stages,
                    "negative_shifts": negative_shifts[:10],
                    "total_negative_shifts": len(negative_shifts),
                },
                "period_days": days,
            }

        except Exception as e:
            logger.error(
                "sentiment_stage_distribution_failed",
                merchant_id=merchant_id,
                days=days,
                error=str(e),
                error_code=7124,
            )
            return {
                "has_data": False,
                "message": "Unable to compute sentiment distribution.",
            }

    async def get_handoff_correlation(self, merchant_id: int, days: int = 30) -> dict[str, Any]:
        """AC5: Correlate conversation intents with human handoff events."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            cutoff_naive = cutoff.replace(tzinfo=None)

            last_turns_before_handoff = (
                select(
                    ConversationTurn.conversation_id,
                    ConversationTurn.intent_detected,
                    ConversationTurn.turn_number,
                    func.row_number()
                    .over(
                        partition_by=ConversationTurn.conversation_id,
                        order_by=ConversationTurn.turn_number.desc(),
                    )
                    .label("rn"),
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.handoff_status.in_(["active", "resolved", "escalated"]))
                .where(ConversationTurn.created_at >= cutoff)
                .subquery()
            )

            trigger_result = await self.db.execute(
                select(
                    last_turns_before_handoff.c.intent_detected,
                    func.count(func.distinct(last_turns_before_handoff.c.conversation_id)).label(
                        "trigger_count"
                    ),
                )
                .where(last_turns_before_handoff.c.rn <= 3)
                .where(last_turns_before_handoff.c.intent_detected != None)  # noqa: E711
                .group_by(last_turns_before_handoff.c.intent_detected)
                .order_by(
                    func.count(func.distinct(last_turns_before_handoff.c.conversation_id)).desc()
                )
                .limit(5)
            )
            top_triggers = [
                {"intent": row.intent_detected, "count": row.trigger_count}
                for row in trigger_result
            ]

            handoff_length_result = await self.db.execute(
                select(func.avg(ConversationTurn.turn_number))
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.handoff_status.in_(["active", "resolved", "escalated"]))
                .where(ConversationTurn.created_at >= cutoff)
            )
            avg_handoff_length = handoff_length_result.scalar()

            handoff_count_result = await self.db.execute(
                select(func.count(func.distinct(Conversation.id)))
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.handoff_status.in_(["active", "resolved", "escalated"]))
                .where(Conversation.created_at >= cutoff_naive)
            )
            handoff_count = handoff_count_result.scalar() or 0

            if handoff_count == 0 and not top_triggers:
                return {
                    "has_data": False,
                    "message": "No handoff conversations in this period.",
                }

            resolved_conv_lengths: list[float] = []
            resolved_stmt = (
                select(
                    ConversationTurn.conversation_id,
                    func.count(ConversationTurn.id).label("turn_count"),
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.handoff_status == "none")
                .where(ConversationTurn.created_at >= cutoff)
                .group_by(ConversationTurn.conversation_id)
            )
            resolved_result = await self.db.execute(resolved_stmt)
            for row in resolved_result:
                resolved_conv_lengths.append(float(row.turn_count))
            avg_resolved_length = (
                round(sum(resolved_conv_lengths) / len(resolved_conv_lengths), 1)
                if resolved_conv_lengths
                else 0
            )

            intent_total_result = await self.db.execute(
                select(
                    ConversationTurn.intent_detected,
                    func.count(func.distinct(ConversationTurn.conversation_id)).label("conv_count"),
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
                .where(ConversationTurn.intent_detected != None)  # noqa: E711
                .group_by(ConversationTurn.intent_detected)
            )
            intent_totals = {row.intent_detected: row.conv_count for row in intent_total_result}

            handoff_rate_per_intent = []
            for trigger in top_triggers:
                total_for_intent = intent_totals.get(trigger["intent"], 0)
                rate = (
                    round(trigger["count"] / total_for_intent * 100, 1)
                    if total_for_intent > 0
                    else 0
                )
                handoff_rate_per_intent.append(
                    {
                        "intent": trigger["intent"],
                        "handoff_count": trigger["count"],
                        "total_count": total_for_intent,
                        "handoff_rate": rate,
                    }
                )

            excerpt_result = await self.db.execute(
                select(
                    ConversationTurn.user_message,
                    ConversationTurn.intent_detected,
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(Conversation.handoff_status.in_(["active", "resolved", "escalated"]))
                .where(ConversationTurn.created_at >= cutoff)
                .where(ConversationTurn.user_message != None)  # noqa: E711
                .limit(5)
            )
            anonymized_excerpts = []
            for row in excerpt_result:
                msg = (row.user_message or "")[:100]
                anonymized_excerpts.append(
                    {
                        "anonymized_message": msg,
                        "intent_detected": row.intent_detected,
                    }
                )

            return {
                "has_data": True,
                "data": {
                    "top_triggers": top_triggers,
                    "avg_handoff_length": round(float(avg_handoff_length), 1)
                    if avg_handoff_length
                    else 0,
                    "avg_resolved_length": avg_resolved_length,
                    "handoff_rate_per_intent": handoff_rate_per_intent,
                    "anonymized_excerpts": anonymized_excerpts,
                    "privacy_note": "Conversation excerpts are anonymized for privacy",
                    "total_handoff_conversations": handoff_count,
                },
                "period_days": days,
            }

        except Exception as e:
            logger.error(
                "handoff_correlation_failed",
                merchant_id=merchant_id,
                days=days,
                error=str(e),
                error_code=7125,
            )
            return {
                "has_data": False,
                "message": "Unable to compute handoff correlation.",
            }

    async def get_context_utilization(self, merchant_id: int, days: int = 30) -> dict[str, Any]:
        """AC6: Context utilization rate — % turns with context reference, by mode."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            total_result = await self.db.execute(
                select(func.count(ConversationTurn.id))
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
            )
            total_turns = total_result.scalar() or 0

            if total_turns == 0:
                return {
                    "has_data": False,
                    "message": "No context utilization data available.",
                }

            with_context_result = await self.db.execute(
                select(func.count(ConversationTurn.id))
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
                .where(
                    ConversationTurn.context_snapshot["has_context_reference"].as_boolean()
                    == True  # noqa: E712
                )
            )
            turns_with_context = with_context_result.scalar() or 0

            utilization_rate = round(turns_with_context / total_turns * 100, 1)

            mode_expr = ConversationTurn.context_snapshot["mode"].astext
            mode_result = await self.db.execute(
                select(
                    mode_expr.label("mode"),
                    func.count(ConversationTurn.id).label("total"),
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
                .where(mode_expr != None)  # noqa: E711
                .group_by(mode_expr)
            )
            by_mode_total = {row.mode: row.total for row in mode_result}

            mode_context_result = await self.db.execute(
                select(
                    mode_expr.label("mode"),
                    func.count(ConversationTurn.id).label("with_context"),
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
                .where(mode_expr != None)  # noqa: E711
                .where(
                    ConversationTurn.context_snapshot["has_context_reference"].as_boolean()
                    == True  # noqa: E712
                )
                .group_by(mode_expr)
            )
            by_mode_with_context = {row.mode: row.with_context for row in mode_context_result}

            by_mode = []
            for mode, total in by_mode_total.items():
                with_ctx = by_mode_with_context.get(mode, 0)
                by_mode.append(
                    {
                        "mode": mode,
                        "total_turns": total,
                        "turns_with_context": with_ctx,
                        "utilization_rate": round(with_ctx / total * 100, 1) if total > 0 else 0,
                    }
                )

            low_util_result = await self.db.execute(
                select(
                    ConversationTurn.conversation_id,
                    func.count(ConversationTurn.id).label("total_turns"),
                    func.sum(
                        case(
                            (
                                ConversationTurn.context_snapshot[
                                    "has_context_reference"
                                ].as_boolean()
                                == True,  # noqa: E712
                                1,
                            ),
                            else_=0,
                        )
                    ).label("context_turns"),
                )
                .join(Conversation, ConversationTurn.conversation_id == Conversation.id)
                .where(Conversation.merchant_id == merchant_id)
                .where(ConversationTurn.created_at >= cutoff)
                .group_by(ConversationTurn.conversation_id)
                .having(
                    func.sum(
                        case(
                            (
                                ConversationTurn.context_snapshot[
                                    "has_context_reference"
                                ].as_boolean()
                                == True,  # noqa: E712
                                1,
                            ),
                            else_=0,
                        )
                    )
                    < func.count(ConversationTurn.id) * 0.5
                )
            )
            low_util_conversations = [
                {
                    "conversation_id": row.conversation_id,
                    "total_turns": row.total_turns,
                    "context_turns": row.context_turns,
                    "utilization_rate": round(row.context_turns / row.total_turns * 100, 1)
                    if row.total_turns > 0
                    else 0,
                }
                for row in low_util_result
            ]

            return {
                "has_data": True,
                "data": {
                    "utilization_rate": utilization_rate,
                    "total_turns": total_turns,
                    "turns_with_context": turns_with_context,
                    "by_mode": by_mode,
                    "low_utilization_conversations": low_util_conversations,
                    "improvement_opportunities": len(low_util_conversations),
                },
                "period_days": days,
            }

        except Exception as e:
            logger.error(
                "context_utilization_failed",
                merchant_id=merchant_id,
                days=days,
                error=str(e),
                error_code=7126,
            )
            return {
                "has_data": False,
                "message": "Unable to compute context utilization.",
            }
