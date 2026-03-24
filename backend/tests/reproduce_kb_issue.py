
import asyncio

import pytest
from fastapi import BackgroundTasks, FastAPI
from httpx import ASGITransport, AsyncClient

# Minimal app for reproduction
app = FastAPI()

@app.post("/test-upload")
async def test_upload(background_tasks: BackgroundTasks):
    async def bg_task():
        await asyncio.sleep(0.1)
        print("Background task running")

    background_tasks.add_task(bg_task)
    return {"status": "ok"}

@pytest.mark.asyncio
async def test_background_tasks_issue():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # This mirrors the knowledge base test structure
        response = await client.post("/test-upload")
        assert response.status_code == 200
        # The issue happens when the test loop closes but background tasks are still pending
        # or when middleware interacts with the loop in a specific way
