import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.models.handoff_alert import HandoffAlert
from app.api.handoff_alerts import _alert_to_response


async def test_wait_time_calculation():
    print("Testing wait time calculation...")

    # Create an alert created 5 minutes ago
    created_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    alert = HandoffAlert(
        id=1,
        merchant_id=1,
        conversation_id=1,
        urgency_level="high",
        wait_time_seconds=0,  # Default in DB
        created_at=created_at,
        is_read=False,
    )

    response = _alert_to_response(alert)

    print(f"Created at: {created_at}")
    print(f"Stored wait_time_seconds: {alert.wait_time_seconds}")
    print(f"Response wait_time_seconds: {response.wait_time_seconds}")

    if response.wait_time_seconds == 0:
        print("FAIL: Wait time is 0 in response!")
    elif response.wait_time_seconds >= 300:
        print(f"PASS: Wait time is {response.wait_time_seconds}s (>= 300s)")
    else:
        print(f"WARN: Wait time is {response.wait_time_seconds}s (unexpected)")


if __name__ == "__main__":
    asyncio.run(test_wait_time_calculation())
