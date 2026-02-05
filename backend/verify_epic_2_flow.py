import os
import asyncio
import json
import httpx
from unittest.mock import MagicMock, AsyncMock, patch
import sys

# Setup environment variables first
os.environ["IS_TESTING"] = "true"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["SECRET_KEY"] = "mock-testing-secret"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost/db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SHOPIFY_APP_API_SECRET"] = "dummy"
os.environ["FACEBOOK_APP_SECRET"] = "dummy"


# Mock Redis (rudimentary async mock)
class MockAsyncRedis:
    def __init__(self, *args, **kwargs):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value):
        self.store[key] = value

    async def setex(self, key, time, value):
        self.store[key] = value

    async def expire(self, key, time):
        pass

    async def delete(self, key):
        if key in self.store:
            del self.store[key]

    async def close(self):
        pass

    async def ping(self):
        return True

    async def exists(self, key):
        return 1 if key in self.store else 0


# Mock Redis (synchronous)
class MockSyncRedis:
    def __init__(self, *args, **kwargs):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

    def setex(self, key, time, value):
        self.store[key] = value

    def expire(self, key, time):
        pass

    def delete(self, key):
        if key in self.store:
            del self.store[key]

    def close(self):
        pass

    def ping(self):
        return True

    def exists(self, key):
        return 1 if key in self.store else 0


mock_async_redis = MockAsyncRedis()
mock_sync_redis = MockSyncRedis()

# Start patches globally for the script
patcher_async = patch("redis.asyncio.from_url", return_value=mock_async_redis)
patcher_sync = patch("redis.from_url", return_value=mock_sync_redis)
patcher_async.start()
patcher_sync.start()

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_csrf_token():
    # Attempt to get CSRF token from a GET request (e.g. root or a dedicated csrf-token endpoint)
    # The middleware usually sets a cookie on GET requests.
    response = client.get("/api/v1/csrf-token")  # Assuming this exists or works
    if response.status_code != 200:
        # Fallback if specific endpoint fails or doesn't exist, try root
        response = client.get("/")
    return response.cookies.get("csrf_token")


def run_flow_verification():
    print("--- Starting Epic 2 Manual Flow Verification (Simulated) ---")

    csrf_token = get_csrf_token()
    headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}
    print(f"[Setup] CSRF Token: {csrf_token}")

    # 1. Product Search
    print("\n[Action] User asks: 'What running shoes do you have under $100?'")
    response = client.post(
        "/api/llm/chat",
        json={"message": "What running shoes do you have under $100?"},
        headers=headers,
        cookies={"csrf_token": csrf_token} if csrf_token else None,
    )

    if response.status_code == 200:
        data = response.json().get("data", {})
        print(f"[Success] Bot Response: {data.get('response', 'No response text')}")
        # Verify content contains key product info from mock
        resp_text = data.get("response", "").lower()
        if "shoes" in resp_text:
            print("[Check] \u2705 Response mentions relevant products")
        else:
            print(f"[Check] \u274c Response content unexpected: {resp_text}")
    else:
        print(f"[Failure] Status {response.status_code}: {response.text}")

    # 2. Add to Cart (Mock LLM response for "add to cart")
    print("\n[Action] User asks: 'Add the running shoes to my cart'")
    # Note: State is maintained because we use the same client/app instance and MockRedis instance
    response = client.post(
        "/api/llm/chat",
        json={"message": "Add to cart"},
        headers=headers,
        cookies={"csrf_token": csrf_token} if csrf_token else None,
    )

    if response.status_code == 200:
        data = response.json().get("data", {})
        print(f"[Success] Bot Response: {data.get('response')}")
        if "added" in str(data.get("response", "")).lower():
            print("[Check] \u2705 Response confirms addition")
        else:
            print("[Check] \u274c Response does not confirm addition")
    else:
        print(f"[Failure] Status {response.status_code}: {response.text}")

    # 3. View Cart
    print("\n[Action] User asks: 'Show my cart'")
    response = client.post(
        "/api/llm/chat",
        json={"message": "Show my cart"},
        headers=headers,
        cookies={"csrf_token": csrf_token} if csrf_token else None,
    )
    if response.status_code == 200:
        data = response.json().get("data", {})
        print(f"[Success] Bot Response: {data.get('response')}")
        if "cart" in str(data.get("response", "")).lower():
            print("[Check] \u2705 Bot acknowledges cart view")
    else:
        print(f"[Failure] Status {response.status_code}: {response.text}")

    # 4. Checkout
    print("\n[Action] User asks: 'Checkout'")
    response = client.post(
        "/api/llm/chat",
        json={"message": "Checkout"},
        headers=headers,
        cookies={"csrf_token": csrf_token} if csrf_token else None,
    )
    if response.status_code == 200:
        data = response.json().get("data", {})
        print(f"[Success] Bot Response: {data.get('response')}")
        if "checkout" in str(data.get("response", "")).lower():
            print("[Check] \u2705 Bot provides checkout info")
    else:
        print(f"[Failure] Status {response.status_code}: {response.text}")


if __name__ == "__main__":
    run_flow_verification()
