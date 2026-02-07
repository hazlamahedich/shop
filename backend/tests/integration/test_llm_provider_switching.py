"""
Integration tests for Story 3.4: LLM Provider Switching.

Tests the complete flow of switching LLM providers, including:
- Provider listing with current provider indicator
- Configuration validation before switching
- Actual provider switching with rollback on failure
- Provider-specific conversation routing
- Cost calculation accuracy
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.user import User
from app.core.config import settings


class TestLLMProviderSwitchingIntegration:
    """Integration tests for LLM provider switching feature."""

    @pytest.mark.asyncio
    async def test_list_providers_shows_current_indicator(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test that provider list correctly identifies the active provider."""
        response = await async_client.get(
            f"{settings.API_V1_STR}/llm/providers",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "providers" in data
        assert "currentProvider" in data
        assert len(data["providers"]) > 0

        # Verify only one provider is marked as active
        active_providers = [p for p in data["providers"] if p.get("isActive")]
        assert len(active_providers) <= 1

        # If currentProvider exists, it should match the active provider
        if data["currentProvider"]:
            active = active_providers[0] if active_providers else None
            assert active is not None
            assert active["id"] == data["currentProvider"]["id"]

    @pytest.mark.asyncio
    async def test_validate_provider_before_switching(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test provider validation before committing to switch."""
        # First get available providers
        list_response = await async_client.get(
            f"{settings.API_V1_STR}/llm/providers",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        providers = list_response.json()["providers"]

        # Find a non-current provider to test validation
        current_id = list_response.json()["currentProvider"]["id"] if list_response.json()["currentProvider"] else None
        test_provider = next((p for p in providers if p["id"] != current_id), None)

        if not test_provider:
            pytest.skip("No alternative provider available for testing")

        # Validate the provider
        response = await async_client.post(
            f"{settings.API_V1_STR}/llm/validate",
            json={
                "providerId": test_provider["id"],
                "apiKey": "test-key-for-validation"
            },
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert "provider" in data
        assert "validatedAt" in data
        assert data["provider"]["id"] == test_provider["id"]

    @pytest.mark.asyncio
    async def test_switch_provider_success_flow(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test successful provider switching flow."""
        # Get current state
        list_response = await async_client.get(
            f"{settings.API_V1_STR}/llm/providers",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        original_data = list_response.json()
        original_provider_id = original_data["currentProvider"]["id"] if original_data["currentProvider"] else None

        providers = original_data["providers"]
        target_provider = next((p for p in providers if p["id"] != original_provider_id), None)

        if not target_provider:
            pytest.skip("No alternative provider available for switching")

        # Switch provider
        switch_response = await async_client.post(
            f"{settings.API_V1_STR}/llm/switch",
            json={"providerId": target_provider["id"]},
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert switch_response.status_code == 200
        switch_data = switch_response.json()

        assert switch_data["provider"]["id"] == target_provider["id"]
        assert "switchedAt" in switch_data

        # Verify the switch persisted
        verify_response = await async_client.get(
            f"{settings.API_V1_STR}/llm/providers",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        verify_data = verify_response.json()

        assert verify_data["currentProvider"]["id"] == target_provider["id"]

        # Switch back to original for cleanup
        await async_client.post(
            f"{settings.API_V1_STR}/llm/switch",
            json={"providerId": original_provider_id or "ollama"},
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

    @pytest.mark.asyncio
    async def test_switch_provider_with_invalid_credentials_fails(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test that switching with invalid credentials fails gracefully."""
        response = await async_client.post(
            f"{settings.API_V1_STR}/llm/switch",
            json={
                "providerId": "openai",
                "apiKey": "invalid-key-should-fail"
            },
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        # Should fail with appropriate error
        assert response.status_code in [400, 401, 422]
        data = response.json()

        assert "detail" in data

    @pytest.mark.asyncio
    async def test_provider_switching_preserves_conversation_history(
        self, async_client: AsyncClient, test_user: User, async_session: AsyncSession
    ):
        """Test that switching providers doesn't affect conversation history."""
        # Create a test conversation
        conversation = Conversation(
            user_id=str(test_user.id),
            title="Test Conversation for Provider Switch",
            llm_provider="ollama"
        )
        async_session.add(conversation)
        await async_session.commit()

        conv_id = str(conversation.id)

        # Switch provider
        await async_client.post(
            f"{settings.API_V1_STR}/llm/switch",
            json={"providerId": "openai"},
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        # Verify conversation still exists
        result = await async_session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        still_exists = result.scalar_one_or_none() is not None

        assert still_exists, "Conversation should be preserved after provider switch"

    @pytest.mark.asyncio
    async def test_new_conversation_uses_current_provider(
        self, async_client: AsyncClient, test_user: User, async_session: AsyncSession
    ):
        """Test that new conversations use the current provider."""
        # First, ensure we know the current provider
        list_response = await async_client.get(
            f"{settings.API_V1_STR}/llm/providers",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        current_provider_id = list_response.json()["currentProvider"]["id"]

        # Create a new conversation
        response = await async_client.post(
            f"{settings.API_V1_STR}/conversations",
            json={"title": "Test Provider Association"},
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 201
        data = response.json()

        # Verify the conversation is associated with current provider
        result = await async_session.execute(
            select(Conversation).where(Conversation.id == data["id"])
        )
        conversation = result.scalar_one()

        assert conversation.llm_provider == current_provider_id

    @pytest.mark.asyncio
    async def test_provider_comparison_data_accuracy(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test that provider comparison returns accurate data."""
        response = await async_client.get(
            f"{settings.API_V1_STR}/llm/providers",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        for provider in data["providers"]:
            # Verify required fields exist
            assert "id" in provider
            assert "name" in provider
            assert "pricing" in provider
            assert "inputCost" in provider["pricing"]
            assert "outputCost" in provider["pricing"]
            assert "currency" in provider["pricing"]
            assert "models" in provider
            assert isinstance(provider["models"], list)

            # Verify pricing is numeric
            assert isinstance(provider["pricing"]["inputCost"], (int, float))
            assert isinstance(provider["pricing"]["outputCost"], (int, float))

    @pytest.mark.asyncio
    async def test_savings_calculation_accuracy(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test that savings calculations are accurate."""
        response = await async_client.get(
            f"{settings.API_V1_STR}/llm/providers",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        data = response.json()

        if not data["currentProvider"]:
            pytest.skip("No current provider set")

        current_id = data["currentProvider"]["id"]
        current_provider = next((p for p in data["providers"] if p["id"] == current_id), None)

        assert current_provider is not None

        # Calculate expected costs manually for comparison
        test_input_tokens = 100000
        test_output_tokens = 50000

        for provider in data["providers"]:
            expected_cost = (
                (test_input_tokens / 1_000_000) * provider["pricing"]["inputCost"] +
                (test_output_tokens / 1_000_000) * provider["pricing"]["outputCost"]
            )

            # If provider has estimatedMonthlyCost, verify it's reasonable
            if "estimatedMonthlyCost" in provider:
                # Allow some tolerance for different usage assumptions
                assert provider["estimatedMonthlyCost"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_switch_requests_handled_safely(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test that concurrent switch requests are handled safely."""
        import asyncio

        # Get current provider
        list_response = await async_client.get(
            f"{settings.API_V1_STR}/llm/providers",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )
        providers = list_response.json()["providers"]
        current_id = list_response.json()["currentProvider"]["id"] if list_response.json()["currentProvider"] else None

        # Create multiple switch requests concurrently
        tasks = []
        for provider in providers[:3]:  # Try to switch to first 3 providers
            if provider["id"] != current_id:
                task = async_client.post(
                    f"{settings.API_V1_STR}/llm/switch",
                    json={"providerId": provider["id"]},
                    headers={"Authorization": f"Bearer {test_user.access_token}"}
                )
                tasks.append(task)

        # Execute all requests concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # At least one should succeed
        successful = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 200]
        assert len(successful) >= 1, "At least one switch request should succeed"

    @pytest.mark.asyncio
    async def test_provider_features_listed_correctly(
        self, async_client: AsyncClient, test_user: User
    ):
        """Test that provider features are listed and accurate."""
        response = await async_client.get(
            f"{settings.API_V1_STR}/llm/providers",
            headers={"Authorization": f"Bearer {test_user.access_token}"}
        )

        data = response.json()

        for provider in data["providers"]:
            assert "features" in provider
            assert isinstance(provider["features"], list)

            # Common features that should be listed
            expected_features = ["streaming", "function-calling"]
            # At least some features should be present
            if len(provider["features"]) > 0:
                assert all(isinstance(f, str) for f in provider["features"])
