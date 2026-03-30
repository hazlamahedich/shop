#!/usr/bin/env python3
"""Test script for FAQ click tracking."""

import asyncio
import requests
import json

BASE_URL = "http://localhost:8000"

def test_faq_click_tracking():
    """Test FAQ click tracking endpoint."""
    print("🧪 Testing FAQ Click Tracking\n")

    # Step 1: Create a widget session
    print("1️⃣ Creating widget session...")
    session_response = requests.post(
        f"{BASE_URL}/api/v1/widget/session",
        json={"merchant_id": "1"}
    )

    if session_response.status_code == 200:
        session_data = session_response.json()
        session_id = session_data.get("data", {}).get("sessionId") or session_data.get("data", {}).get("session_id")
        print(f"✅ Session created: {session_id}")
    else:
        print(f"❌ Failed to create session: {session_response.status_code}")
        print(session_response.text)
        return

    # Step 2: Get FAQ buttons
    print("\n2️⃣ Getting FAQ buttons...")
    faq_response = requests.get(f"{BASE_URL}/api/v1/widget/faq-buttons/1")

    if faq_response.status_code == 200:
        faq_data = faq_response.json()
        faqs = faq_data.get("data", {}).get("buttons", [])
        print(f"✅ Found {len(faqs)} FAQ buttons")

        if faqs:
            first_faq = faqs[0]
            faq_id = first_faq.get("id")
            print(f"   Testing with FAQ: {first_faq.get('question', 'N/A')}")

            # Step 3: Track FAQ click
            print(f"\n3️⃣ Tracking FAQ click for FAQ ID {faq_id}...")
            click_response = requests.post(
                f"{BASE_URL}/api/v1/widget/faq-click",
                json={
                    "faq_id": faq_id,
                    "session_id": session_id,
                    "merchant_id": 1
                }
            )

            print(f"   Response status: {click_response.status_code}")

            if click_response.status_code == 200:
                click_data = click_response.json()
                print(f"✅ FAQ click tracked successfully!")
                print(f"   Success: {click_data.get('data', {}).get('success')}")
                print(f"   Click ID: {click_data.get('data', {}).get('clickId')}")
            else:
                print(f"❌ Failed to track FAQ click")
                print(f"   Error: {click_response.text}")

                # Try with merchant_id as string
                print(f"\n🔄 Retrying with merchant_id as string...")
                click_response2 = requests.post(
                    f"{BASE_URL}/api/v1/widget/faq-click",
                    json={
                        "faq_id": faq_id,
                        "session_id": session_id,
                        "merchant_id": "1"
                    }
                )

                if click_response2.status_code == 200:
                    click_data = click_response2.json()
                    print(f"✅ FAQ click tracked successfully (with string merchant_id)!")
                    print(f"   Success: {click_data.get('data', {}).get('success')}")
                else:
                    print(f"❌ Still failed: {click_response2.text}")
        else:
            print("⚠️  No FAQ buttons found")
    else:
        print(f"❌ Failed to get FAQ buttons: {faq_response.status_code}")
        print(faq_response.text)

    print("\n" + "="*50)
    print("Test complete!")

if __name__ == "__main__":
    try:
        test_faq_click_tracking()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
