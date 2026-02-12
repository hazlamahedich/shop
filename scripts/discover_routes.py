import requests
import json

BASE_URL = "http://localhost:8000"


def check_routes():
    print(f"Checking routes at {BASE_URL}...")

    # Try common prefixes
    prefixes = ["", "/api", "/api/v1"]
    endpoints = ["/costs/summary", "/merchant/settings", "/health", "/conversations"]

    for prefix in prefixes:
        for endpoint in endpoints:
            url = f"{BASE_URL}{prefix}{endpoint}"
            try:
                response = requests.get(url, timeout=2)
                print(f"[{response.status_code}] {url}")
            except Exception as e:
                print(f"[ERR] {url}: {e}")


if __name__ == "__main__":
    check_routes()
