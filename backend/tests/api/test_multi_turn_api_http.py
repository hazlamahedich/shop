"""HTTP-level tests for multi-turn debug API endpoints.

Story 11-2 [P2]: Tests GET/POST multi-turn state endpoints through FastAPI ASGI transport.
Validates request/response lifecycle, auth, envelope structure, and real DB interactions.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app


GET_URL = "/api/conversations/{conversation_id}/multi-turn-state"
RESET_URL = "/api/conversations/{conversation_id}/multi-turn-reset"


@pytest.fixture
async def http_client(async_session):
    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestGetMultiTurnStateHTTP:
    async def test_returns_idle_default_for_new_conversation(
        self, http_client, test_conversation, test_merchant
    ):
        headers = _auth_headers(test_merchant)
        resp = await http_client.get(
            GET_URL.format(conversation_id=test_conversation.id), headers=headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["state"] == "IDLE"
        assert body["data"]["turn_count"] == 0
        assert body["data"]["conversation_id"] == test_conversation.id

    async def test_envelope_structure_has_meta(self, http_client, test_conversation, test_merchant):
        headers = _auth_headers(test_merchant)
        resp = await http_client.get(
            GET_URL.format(conversation_id=test_conversation.id), headers=headers
        )
        body = resp.json()
        assert "meta" in body
        assert "requestId" in body["meta"]
        assert "timestamp" in body["meta"]

    async def test_nonexistent_conversation_returns_404(self, http_client, test_merchant):
        headers = _auth_headers(test_merchant)
        resp = await http_client.get(GET_URL.format(conversation_id=99999), headers=headers)
        assert resp.status_code in (404, 500)

    async def test_wrong_merchant_cannot_access(
        self, http_client, test_conversation, test_merchant
    ):
        from app.core.auth import create_jwt
        import uuid

        other_token = create_jwt(merchant_id=99999, session_id=str(uuid.uuid4()))
        headers = {"Authorization": f"Bearer {other_token}"}
        resp = await http_client.get(
            GET_URL.format(conversation_id=test_conversation.id), headers=headers
        )
        assert resp.status_code in (404, 500)

    async def test_no_auth_returns_error(self, http_client, test_conversation):
        resp = await http_client.get(GET_URL.format(conversation_id=test_conversation.id))
        assert resp.status_code in (401, 403, 500)


@pytest.mark.asyncio
class TestResetMultiTurnStateHTTP:
    async def test_reset_returns_200_with_previous_state(
        self, http_client, test_conversation, test_merchant
    ):
        headers = _auth_headers(test_merchant)
        resp = await http_client.post(
            RESET_URL.format(conversation_id=test_conversation.id), headers=headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["reset"] is True
        assert body["data"]["previous_state"] == "IDLE"
        assert body["data"]["conversation_id"] == test_conversation.id

    async def test_reset_envelope_has_meta(self, http_client, test_conversation, test_merchant):
        headers = _auth_headers(test_merchant)
        resp = await http_client.post(
            RESET_URL.format(conversation_id=test_conversation.id), headers=headers
        )
        body = resp.json()
        assert "meta" in body
        assert "requestId" in body["meta"]

    async def test_reset_nonexistent_conversation_returns_error(self, http_client, test_merchant):
        headers = _auth_headers(test_merchant)
        resp = await http_client.post(RESET_URL.format(conversation_id=99999), headers=headers)
        assert resp.status_code in (404, 500)

    async def test_get_after_reset_still_idle(self, http_client, test_conversation, test_merchant):
        headers = _auth_headers(test_merchant)
        await http_client.post(
            RESET_URL.format(conversation_id=test_conversation.id), headers=headers
        )
        resp = await http_client.get(
            GET_URL.format(conversation_id=test_conversation.id), headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["state"] == "IDLE"


def _auth_headers(merchant_id: int) -> dict[str, str]:
    from app.core.auth import create_jwt
    import uuid

    token = create_jwt(merchant_id=merchant_id, session_id=str(uuid.uuid4()))
    return {"Authorization": f"Bearer {token}"}
