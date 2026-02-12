import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
MERCHANT_ID = 1
HEADERS = {
    "X-Merchant-Id": str(MERCHANT_ID),
    "Content-Type": "application/json",
    "X-Test-Mode": "true",
}


def log_test(name, success, data=None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"[{status}] {name}")
    if data:
        print(f"   Data: {json.dumps(data, indent=2)}")


def test_merchant_settings():
    print("\n--- Testing Merchant Settings ---")

    # 1. Get settings
    response = requests.get(f"{BASE_URL}/api/merchant/settings", headers=HEADERS)
    log_test("GET /api/merchant/settings", response.status_code == 200, response.json())

    # 2. Update settings (budget cap)
    new_budget = 75.0
    # Payload must match expected Body(..., embed=True)
    payload = {"budget_cap": new_budget}

    response = requests.patch(f"{BASE_URL}/api/merchant/settings", headers=HEADERS, json=payload)
    log_test(
        "PATCH /api/merchant/settings (budget_cap=75.0)",
        response.status_code == 200,
        response.json(),
    )

    # 3. Verify update
    response = requests.get(f"{BASE_URL}/api/merchant/settings", headers=HEADERS)
    success = response.status_code == 200 and response.json().get("budget_cap") == new_budget
    log_test("Verify budget_cap update", success, response.json())


def test_cost_summary():
    print("\n--- Testing Cost Summary ---")

    # 1. Get summary (all time/default)
    response = requests.get(f"{BASE_URL}/api/costs/summary", headers=HEADERS)
    log_test("GET /api/costs/summary", response.status_code == 200, response.json())

    # 2. Get summary with date range (last 30 days)
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    response = requests.get(
        f"{BASE_URL}/api/costs/summary",
        headers=HEADERS,
        params={"date_from": date_from, "date_to": date_to},
    )
    log_test(
        f"GET /api/costs/summary (last 30 days: {date_from} to {date_to})",
        response.status_code == 200,
        response.json(),
    )


def test_conversation_costs():
    print("\n--- Testing Conversation Costs ---")

    summary_response = requests.get(f"{BASE_URL}/api/costs/summary", headers=HEADERS)
    summary_data = summary_response.json().get("data", {})
    # The summary data structure in service (mock for now if no business logic)
    # topConversations is likely the field
    conversations = summary_data.get("topConversations", [])

    if conversations:
        conv_id = conversations[0].get("conversationId")
        print(f"Testing for conversation ID: {conv_id}")
        response = requests.get(f"{BASE_URL}/api/costs/conversation/{conv_id}", headers=HEADERS)
        log_test(
            f"GET /api/costs/conversation/{conv_id}",
            response.status_code == 200,
            response.json(),
        )
    else:
        print("[!] No conversations found in summary to test specific conversation costs.")
        print(f"Available summary data keys: {list(summary_data.keys())}")


if __name__ == "__main__":
    try:
        test_merchant_settings()
        test_cost_summary()
        test_conversation_costs()
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"❌ Error during manual verification: {e}")
