"""DLQ Retry Worker for Shopify webhooks.

Story 4-2: Shopify Webhook Integration
Task 6: DLQ retry mechanism with exponential backoff

Processes failed webhooks from the Dead Letter Queue with:
- Exponential backoff (1m, 5m, 15m)
- Max 3 retry attempts
- Structured logging for observability
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

DLQ_QUEUE_KEY = "webhook:dlq:shopify"
DLQ_PROCESSING_KEY = "webhook:dlq:shopify:processing"

BACKOFF_DELAYS = [60, 300, 900]  # 1 min, 5 min, 15 min in seconds
MAX_RETRY_ATTEMPTS = 3
BATCH_SIZE = 100


class DLQRetryWorker:
    """Worker for processing failed Shopify webhooks from DLQ."""

    def __init__(self) -> None:
        self._running = False
        self._redis_client = None

    def _get_redis_client(self):
        """Get or create Redis client."""
        if self._redis_client is None:
            import redis

            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                self._redis_client = redis.from_url(redis_url, decode_responses=True)
        return self._redis_client

    async def process_dlq_batch(self) -> dict[str, Any]:
        """Process a batch of webhooks from the DLQ.

        Returns:
            Dict with processing stats: processed, succeeded, failed, max_retries
        """
        redis_client = self._get_redis_client()
        if not redis_client:
            logger.warning("dlq_worker_no_redis")
            return {"processed": 0, "succeeded": 0, "failed": 0, "max_retries": 0}

        stats = {"processed": 0, "succeeded": 0, "failed": 0, "max_retries": 0}

        for _ in range(BATCH_SIZE):
            result = redis_client.lpop(DLQ_QUEUE_KEY)
            if not result:
                break

            try:
                retry_data = json.loads(result)
                stats["processed"] += 1

                should_retry, retry_after = self._should_retry(retry_data)

                if not should_retry:
                    stats["max_retries"] += 1
                    self._log_max_retries_exceeded(retry_data)
                    continue

                if retry_after > 0:
                    self._requeue_with_delay(redis_client, retry_data, retry_after)
                    continue

                success = await self._process_webhook(retry_data)

                if success:
                    stats["succeeded"] += 1
                else:
                    stats["failed"] += 1
                    self._increment_and_requeue(redis_client, retry_data)

            except json.JSONDecodeError as e:
                logger.error("dlq_worker_invalid_json", error=str(e))
                stats["failed"] += 1
            except Exception as e:
                logger.error("dlq_worker_unexpected_error", error=str(e))
                stats["failed"] += 1

        logger.info("dlq_batch_processed", **stats)
        return stats

    def _should_retry(self, retry_data: dict) -> tuple[bool, int]:
        """Check if webhook should be retried and calculate backoff delay.

        Args:
            retry_data: DLQ entry with attempts, timestamp, etc.

        Returns:
            Tuple of (should_retry: bool, retry_after_seconds: int)
        """
        attempts = retry_data.get("attempts", 0)

        if attempts >= MAX_RETRY_ATTEMPTS:
            return False, 0

        timestamp_str = retry_data.get("timestamp")
        if not timestamp_str:
            return True, 0

        try:
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            queued_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            elapsed = (datetime.utcnow() - queued_time.replace(tzinfo=None)).total_seconds()

            backoff_index = min(attempts, len(BACKOFF_DELAYS) - 1)
            required_delay = BACKOFF_DELAYS[backoff_index]

            if elapsed < required_delay:
                retry_after = int(required_delay - elapsed)
                return True, retry_after

            return True, 0
        except Exception:
            return True, 0

    async def _process_webhook(self, retry_data: dict) -> bool:
        """Process a webhook from the DLQ.

        Args:
            retry_data: DLQ entry with webhook_data and topic

        Returns:
            True if processing succeeded, False otherwise
        """
        webhook_data = retry_data.get("webhook_data", {})
        topic = retry_data.get("topic", "")

        log = logger.bind(
            shopify_order_id=webhook_data.get("id"),
            topic=topic,
            attempt=retry_data.get("attempts", 0) + 1,
        )

        log.info("dlq_webhook_retry_start")

        try:
            from app.api.webhooks.shopify import process_shopify_webhook

            await process_shopify_webhook(
                payload=webhook_data,
                topic=topic,
                shop_domain=retry_data.get("shop_domain", ""),
                request_id=f"dlq-retry-{retry_data.get('timestamp', '')}",
            )

            log.info("dlq_webhook_retry_success")
            return True

        except Exception as e:
            log.warning("dlq_webhook_retry_failed", error=str(e))
            return False

    def _increment_and_requeue(self, redis_client, retry_data: dict) -> None:
        """Increment attempt count and requeue webhook."""
        retry_data["attempts"] = retry_data.get("attempts", 0) + 1
        retry_data["last_error"] = retry_data.get("error", "Unknown error")
        retry_data["retried_at"] = datetime.utcnow().isoformat()

        redis_client.rpush(DLQ_QUEUE_KEY, json.dumps(retry_data))

        logger.info(
            "dlq_webhook_requeued",
            shopify_order_id=retry_data.get("webhook_data", {}).get("id"),
            attempts=retry_data["attempts"],
        )

    def _requeue_with_delay(self, redis_client, retry_data: dict, delay_seconds: int) -> None:
        """Requeue webhook to be processed after delay."""
        retry_data["delayed_until"] = (
            datetime.utcnow() + timedelta(seconds=delay_seconds)
        ).isoformat()

        redis_client.rpush(DLQ_QUEUE_KEY, json.dumps(retry_data))

        logger.debug(
            "dlq_webhook_delayed",
            shopify_order_id=retry_data.get("webhook_data", {}).get("id"),
            delay_seconds=delay_seconds,
        )

    def _log_max_retries_exceeded(self, retry_data: dict) -> None:
        """Log webhook that exceeded max retries."""
        logger.error(
            "dlq_webhook_max_retries_exceeded",
            shopify_order_id=retry_data.get("webhook_data", {}).get("id"),
            topic=retry_data.get("topic"),
            attempts=retry_data.get("attempts", 0),
            original_error=retry_data.get("error"),
        )

    def get_dlq_size(self) -> int:
        """Get current DLQ size.

        Returns:
            Number of items in DLQ, or -1 if Redis unavailable
        """
        redis_client = self._get_redis_client()
        if not redis_client:
            return -1

        try:
            return redis_client.llen(DLQ_QUEUE_KEY)
        except Exception:
            return -1

    def get_dlq_metrics(self) -> dict[str, Any]:
        """Get DLQ metrics for monitoring endpoint.

        Returns:
            Dict with dlq_size and health status
        """
        dlq_size = self.get_dlq_size()

        return {
            "dlq_size": dlq_size,
            "dlq_healthy": dlq_size >= 0 and dlq_size < 10,
            "max_retries": MAX_RETRY_ATTEMPTS,
            "backoff_delays_seconds": BACKOFF_DELAYS,
        }

    async def run_forever(self, interval_seconds: int = 300) -> None:
        """Run the worker continuously, processing DLQ every interval.

        Args:
            interval_seconds: How often to process DLQ (default 5 minutes)
        """
        self._running = True
        logger.info("dlq_worker_started", interval_seconds=interval_seconds)

        while self._running:
            try:
                await self.process_dlq_batch()
            except Exception as e:
                logger.error("dlq_worker_error", error=str(e))

            await asyncio.sleep(interval_seconds)

    def stop(self) -> None:
        """Stop the worker."""
        self._running = False
        logger.info("dlq_worker_stopped")


dlq_worker = DLQRetryWorker()
