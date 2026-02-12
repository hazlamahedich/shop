import requests
import sys

BASE_URL = "http://localhost:8000"


def verify_csrf():
    print("Starting Manual Verification for Story 1-9 (CSRF Token Generation)...")
    session = requests.Session()

    # 1. Get CSRF Token
    print("\n1. Testing GET /api/v1/csrf-token...")
    try:
        response = session.get(f"{BASE_URL}/api/v1/csrf-token")
        if response.status_code != 200:
            print(f"FAILED: Expected 200, got {response.status_code}")
            print(response.text)
            return False

        data = response.json()
        csrf_token = data.get("csrf_token")
        if not csrf_token:
            print("FAILED: No csrf_token in response body")
            return False

        # Check for cookie
        csrf_cookie = None
        for cookie in session.cookies:
            if cookie.name == "csrf_token":
                csrf_cookie = cookie
                break

        if not csrf_cookie:
            print("FAILED: No csrf_token cookie found")
            return False

        print(f"SUCCESS: Got CSRF token: {csrf_token[:10]}...")
        print(f"SUCCESS: Got CSRF cookie: {csrf_cookie.name}")

    except Exception as e:
        print(f"FAILED: Exception fetching token: {e}")
        return False

    # 2. Test CSRF Protection (Failure Case - No Token)
    print("\n2. Testing CSRF Protection (Request WITHOUT token)...")
    try:
        # Using refresh endpoint which should be protected.
        # We need to ensure we don't accidentally send the cookie if testing "no token",
        # BUT the middleware checks for matching header AND cookie.
        # If we send NO cookie, it fails (cookie missing).
        # If we send cookie but NO header, it fails (header missing).

        # Case A: No Cookie, No Header
        res_fail = requests.post(f"{BASE_URL}/api/v1/csrf-token/refresh")

        if res_fail.status_code == 403:
            print("SUCCESS: Request without cookie/header was rejected (403).")
        else:
            print(f"FAILED: Expected 403, got {res_fail.status_code}")
            print(res_fail.text)
            return False

        # Case B: Cookie Present, No Header (using session)
        res_fail_header = session.post(f"{BASE_URL}/api/v1/csrf-token/refresh")
        if res_fail_header.status_code == 403:
            print("SUCCESS: Request with cookie but NO header was rejected (403).")
        else:
            print(f"FAILED: Expected 403 (Missing Header), got {res_fail_header.status_code}")
            print(res_fail_header.text)
            return False

    except Exception as e:
        print(f"FAILED: Exception in negative test: {e}")
        return False

    # 3. Test CSRF Protection (Failure Case - Invalid Token)
    print("\n3. Testing CSRF Protection (Request WITH INVALID token)...")
    try:
        headers = {"X-CSRF-Token": "invalid-token-12345"}
        res_invalid = session.post(f"{BASE_URL}/api/v1/csrf-token/refresh", headers=headers)

        if res_invalid.status_code == 403:
            print("SUCCESS: Request with invalid token was rejected (403).")
        else:
            print(f"FAILED: Expected 403, got {res_invalid.status_code}")
            print(res_invalid.text)
            return False
    except Exception as e:
        print(f"FAILED: Exception in invalid token test: {e}")
        return False

    # 4. Test CSRF Protection (Success Case)
    print("\n4. Testing CSRF Protection (Request WITH VALID token)...")
    try:
        headers = {"X-CSRF-Token": csrf_token}
        res_success = session.post(f"{BASE_URL}/api/v1/csrf-token/refresh", headers=headers)

        if res_success.status_code == 200:
            print("SUCCESS: Request with valid token was accepted (200).")
            new_token = res_success.json().get("csrf_token")
            print(f"SUCCESS: Got refreshed token: {new_token[:10]}...")
        else:
            print(f"FAILED: Expected 200, got {res_success.status_code}")
            print(res_success.text)
            print(f"Sent Headers: {headers}")
            print(f"Sent Cookies: {session.cookies.get_dict()}")
            return False

    except Exception as e:
        print(f"FAILED: Exception in success test: {e}")
        return False

    print("\nVerification Complete: ALL CHECKS PASSED")
    return True


if __name__ == "__main__":
    if verify_csrf():
        sys.exit(0)
    else:
        sys.exit(1)
