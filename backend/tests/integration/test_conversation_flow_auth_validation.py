from __future__ import annotations

import pytest
from httpx import AsyncClient

CONVERSATION_FLOW_ENDPOINTS = [
    "/api/v1/analytics/conversation-flow/length-distribution",
    "/api/v1/analytics/conversation-flow/clarification-patterns",
    "/api/v1/analytics/conversation-flow/friction-points",
    "/api/v1/analytics/conversation-flow/sentiment-stages",
    "/api/v1/analytics/conversation-flow/handoff-correlation",
    "/api/v1/analytics/conversation-flow/context-utilization",
]


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-16")
@pytest.mark.parametrize("endpoint", CONVERSATION_FLOW_ENDPOINTS)
async def test_endpoints_return_success_with_test_mode_headers(
    async_client: AsyncClient, endpoint: str
) -> None:
    response = await async_client.get(
        endpoint,
        headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "has_data" in data


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-17")
async def test_days_param_rejects_zero(async_client: AsyncClient) -> None:
    response = await async_client.get(
        "/api/v1/analytics/conversation-flow/length-distribution",
        params={"days": 0},
        headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
    )
    assert response.status_code == 422


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-18")
async def test_days_param_rejects_over_365(async_client: AsyncClient) -> None:
    response = await async_client.get(
        "/api/v1/analytics/conversation-flow/length-distribution",
        params={"days": 366},
        headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
    )
    assert response.status_code == 422


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-19")
async def test_days_param_rejects_negative(async_client: AsyncClient) -> None:
    response = await async_client.get(
        "/api/v1/analytics/conversation-flow/length-distribution",
        params={"days": -1},
        headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
    )
    assert response.status_code == 422
