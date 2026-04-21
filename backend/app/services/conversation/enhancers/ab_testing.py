"""A/B Testing Framework for Conversations.

Scientific framework for testing conversation improvements
with data-driven decision making.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog
from redis import Redis

logger = structlog.get_logger(__name__)


class TestGroup(str, Enum):
    """A/B test groups."""
    CONTROL = "control"
    TREATMENT = "treatment"


class ABTestFramework:
    """A/B test conversation improvements."""

    REDIS_KEY_PREFIX = "ab_testing"
    REDIS_TTL_SECONDS = 604800  # 7 days

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def assign_test_group(
        self,
        conversation_id: int,
        merchant_id: int,
        test_name: str,
    ) -> str:
        """Assign conversation to A/B test group.

        Args:
            conversation_id: Conversation ID
            merchant_id: Merchant ID
            test_name: Test/experiment name

        Returns:
            Assigned test group ("control" or "treatment")
        """
        # Check if test is enabled for this merchant
        if not await self._is_merchant_opted_in(merchant_id, test_name):
            return TestGroup.CONTROL.value

        # Check if conversation already assigned
        existing_assignment = await self._get_existing_assignment(conversation_id, test_name)
        if existing_assignment:
            return existing_assignment

        # Assign group (50/50 split)
        group = TestGroup.TREATMENT if random.random() < 0.5 else TestGroup.CONTROL

        # Track assignment
        await self._track_assignment(conversation_id, test_name, group.value, merchant_id)

        return group.value

    async def record_test_result(
        self,
        conversation_id: int,
        test_name: str,
        metrics: dict[str, float],
        merchant_id: int,
    ) -> None:
        """Record test results for analysis.

        Args:
            conversation_id: Conversation ID
            test_name: Test/experiment name
            metrics: Quality metrics to record
            merchant_id: Merchant ID
        """
        # Get test group
        group = await self._get_existing_assignment(conversation_id, test_name)

        if not group:
            self.logger.warning(
                "ab_test_no_group_found",
                conversation_id=conversation_id,
                test_name=test_name,
            )
            return

        # Store result with metadata
        result_data = {
            "conversation_id": conversation_id,
            "test_name": test_name,
            "group": group,
            "merchant_id": merchant_id,
            "metrics": metrics,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if self.redis:
            try:
                # Store individual result
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:result:{conversation_id}:{test_name}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(result_data),
                )

                # Store aggregated results for test
                test_key = f"{self.REDIS_KEY_PREFIX}:test:{test_name}"
                test_results = self.redis.get(test_key)
                results_list = json.loads(test_results) if test_results else []

                results_list.append(result_data)
                self.redis.setex(
                    test_key,
                    self.REDIS_TTL_SECONDS,
                    json.dumps(results_list[-1000:]),  # Keep last 1000
                )

                self.logger.info(
                    "ab_test_result_recorded",
                    conversation_id=conversation_id,
                    test_name=test_name,
                    group=group,
                )
            except Exception as e:
                self.logger.error(
                    "ab_test_result_failed",
                    error=str(e),
                    conversation_id=conversation_id,
                    test_name=test_name,
                )

    async def get_test_results(
        self,
        test_name: str,
        merchant_id: int | None = None,
    ) -> dict[str, Any]:
        """Get aggregated test results.

        Args:
            test_name: Test/experiment name
            merchant_id: Optional merchant ID filter

        Returns:
            Aggregated test results with statistics
        """
        if not self.redis:
            return {}

        try:
            test_key = f"{self.REDIS_KEY_PREFIX}:test:{test_name}"
            test_results = self.redis.get(test_key)

            if not test_results:
                return {"test_name": test_name, "results": []}

            results_list = json.loads(test_results)

            # Filter by merchant if specified
            if merchant_id:
                results_list = [r for r in results_list if r.get("merchant_id") == merchant_id]

            # Calculate statistics
            control_results = [r for r in results_list if r.get("group") == "control"]
            treatment_results = [r for r in results_list if r.get("group") == "treatment"]

            if not control_results or not treatment_results:
                return {
                    "test_name": test_name,
                    "results": results_list,
                    "control_count": len(control_results),
                    "treatment_count": len(treatment_results),
                }

            # Calculate statistical significance (simplified)
            control_avg = sum(r["metrics"].get("satisfaction_predictor", 0.5) for r in control_results) / len(control_results)
            treatment_avg = sum(r["metrics"].get("satisfaction_predictor", 0.5) for r in treatment_results) / len(treatment_results)

            improvement = ((treatment_avg - control_avg) / control_avg) * 100 if control_avg > 0 else 0

            return {
                "test_name": test_name,
                "control_count": len(control_results),
                "treatment_count": len(treatment_results),
                "control_avg_satisfaction": control_avg,
                "treatment_avg_satisfaction": treatment_avg,
                "improvement_percent": improvement,
                "is_significant": abs(improvement) > 10,  # 10% threshold
                "results": results_list[:10],  # Return first 10 for display
            }
        except Exception as e:
            self.logger.error(
                "ab_test_results_failed",
                error=str(e),
                test_name=test_name,
            )
            return {}

    async def _is_merchant_opted_in(
        self,
        merchant_id: int,
        test_name: str,
    ) -> bool:
        """Check if merchant is opted in for A/B test.

        Args:
            merchant_id: Merchant ID
            test_name: Test name

        Returns:
            True if opted in
        """
        if not self.redis:
            return False

        try:
            opt_in_key = f"{self.REDIS_KEY_PREFIX}:optin:{merchant_id}:{test_name}"
            return bool(self.redis.get(opt_in_key))
        except Exception:
            return False

    async def _get_existing_assignment(
        self,
        conversation_id: int,
        test_name: str,
    ) -> str | None:
        """Get existing test group assignment.

        Args:
            conversation_id: Conversation ID
            test_name: Test name

        Returns:
            Group assignment if exists
        """
        if not self.redis:
            return None

        try:
            assignment_key = f"{self.REDIS_KEY_PREFIX}:assignment:{conversation_id}:{test_name}"
            assignment = self.redis.get(assignment_key)

            if assignment:
                return json.loads(assignment).get("group")
        except Exception:
            pass

        return None

    async def _track_assignment(
        self,
        conversation_id: int,
        test_name: str,
        group: str,
        merchant_id: int,
    ) -> None:
        """Track test group assignment.

        Args:
            conversation_id: Conversation ID
            test_name: Test name
            group: Assigned group
            merchant_id: Merchant ID
        """
        if self.redis:
            try:
                assignment_data = {
                    "conversation_id": conversation_id,
                    "test_name": test_name,
                    "group": group,
                    "merchant_id": merchant_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:assignment:{conversation_id}:{test_name}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(assignment_data),
                )
            except Exception:
                pass

    async def enable_merchant_for_test(
        self,
        merchant_id: int,
        test_name: str,
        percentage: float = 0.1,  # 10% of traffic
    ) -> bool:
        """Enable merchant for A/B testing.

        Args:
            merchant_id: Merchant ID
            test_name: Test name
            percentage: Percentage of traffic to include (0.0 to 1.0)

        Returns:
            True if enabled successfully
        """
        if not self.redis:
            return False

        try:
            # Check if test is already configured
            config_key = f"{self.REDIS_KEY_PREFIX}:config:{test_name}"
            existing_config = self.redis.get(config_key)

            config = {
                "test_name": test_name,
                "enabled_merchants": [],
                "percentage": percentage,
                "start_date": datetime.now(timezone.utc).isoformat(),
            }

            if existing_config:
                config = json.loads(existing_config)

            if merchant_id not in config["enabled_merchants"]:
                config["enabled_merchants"].append(merchant_id)

                self.redis.setex(
                    config_key,
                    self.REDIS_TTL_SECONDS,
                    json.dumps(config),
                )

                # Set opt-in flag
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:optin:{merchant_id}:{test_name}",
                    self.REDIS_TTL_SECONDS,
                    "1",
                )

                return True
        except Exception as e:
            self.logger.error(
                "ab_test_enable_failed",
                error=str(e),
                merchant_id=merchant_id,
                test_name=test_name,
            )

        return False

    async def get_test_configuration(
        self,
        test_name: str,
    ) -> dict[str, Any] | None:
        """Get test configuration.

        Args:
            test_name: Test name

        Returns:
            Test configuration if exists
        """
        if not self.redis:
            return None

        try:
            config_key = f"{self.REDIS_KEY_PREFIX}:config:{test_name}"
            config = self.redis.get(config_key)

            if config:
                return json.loads(config)
        except Exception:
            pass

        return None

    async def create_experiment(
        self,
        test_name: str,
        description: str,
        hypothesis: str,
        success_criteria: str,
        percentage: float = 0.1,
        duration_days: int = 7,
    ) -> dict[str, Any]:
        """Create new A/B test experiment.

        Args:
            test_name: Test name
            description: Test description
            hypothesis: Test hypothesis
            success_criteria: Success criteria
            percentage: Percentage of traffic to include
            duration_days: Test duration in days

        Returns:
            Created experiment configuration
        """
        if not self.redis:
            return {}

        try:
            experiment = {
                "test_name": test_name,
                "description": description,
                "hypothesis": hypothesis,
                "success_criteria": success_criteria,
                "percentage": percentage,
                "duration_days": duration_days,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
                "enabled_merchants": [],
            }

            self.redis.setex(
                f"{self.REDIS_KEY_PREFIX}:config:{test_name}",
                self.REDIS_TTL_SECONDS * duration_days,
                json.dumps(experiment),
            )

            return experiment
        except Exception as e:
            self.logger.error(
                "ab_test_create_failed",
                error=str(e),
                test_name=test_name,
            )

        return {}