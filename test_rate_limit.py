#!/usr/bin/env python3
"""
Test script for rate limiting functionality.
Tests that the rate limiter correctly blocks requests after the daily limit.
"""

import requests
import time
import sys

BACKEND_URL = "http://localhost:5371"
TEST_ENDPOINT = f"{BACKEND_URL}/analyze/text"
TEST_PAYLOAD = {"text": "Test message for rate limiting"}


def test_rate_limiting(num_requests=12):
    """
    Make multiple requests to test rate limiting.

    Expected behavior:
    - First 10 requests: Should succeed (200 OK)
    - 11th+ requests: Should be rate limited (429 Too Many Requests)
    """
    print(f"Testing rate limiting with {num_requests} requests...")
    print(f"Endpoint: {TEST_ENDPOINT}")
    print(f"Expected limit: 10 requests per day\n")

    successful_requests = 0
    rate_limited_requests = 0

    for i in range(1, num_requests + 1):
        try:
            response = requests.post(
                TEST_ENDPOINT,
                json=TEST_PAYLOAD,
                timeout=10
            )

            if response.status_code == 200:
                successful_requests += 1
                print(f"✅ Request {i}: SUCCESS (200 OK)")

            elif response.status_code == 429:
                rate_limited_requests += 1
                print(f"🚫 Request {i}: RATE LIMITED (429)")
                try:
                    error_detail = response.json().get('detail', {})
                    if isinstance(error_detail, dict):
                        print(f"   Limit: {error_detail.get('limit')}")
                        print(f"   Remaining: {error_detail.get('remaining')}")
                        print(f"   Reset at: {error_detail.get('reset_at')}")
                        print(f"   Message: {error_detail.get('message')}")
                except:
                    print(f"   Response: {response.text}")

            else:
                print(f"❌ Request {i}: UNEXPECTED STATUS {response.status_code}")
                print(f"   Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Request {i}: FAILED - {e}")

        # Small delay between requests
        time.sleep(0.1)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total requests made: {num_requests}")
    print(f"Successful (200): {successful_requests}")
    print(f"Rate limited (429): {rate_limited_requests}")
    print(f"Expected success: 10")
    print(f"Expected rate limited: {max(0, num_requests - 10)}")

    # Validate results
    if successful_requests == 10 and rate_limited_requests == (num_requests - 10):
        print("\n✅ RATE LIMITING WORKS CORRECTLY!")
        return True
    elif successful_requests < 10:
        print("\n⚠️  WARNING: Fewer than 10 successful requests.")
        print("   This might indicate:")
        print("   - Backend is not running")
        print("   - SQL schema not applied")
        print("   - Other API errors")
        return False
    elif successful_requests > 10:
        print("\n❌ RATE LIMITING FAILED!")
        print("   More than 10 requests succeeded.")
        print("   This indicates rate limiting is not working properly.")
        return False
    else:
        print("\n⚠️  UNEXPECTED RESULTS")
        return False


def check_backend_health():
    """Check if the backend is running and healthy."""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"⚠️  Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend is not accessible: {e}")
        print(f"\nMake sure the backend is running:")
        print(f"  cd backend")
        print(f"  python run_backend.py")
        return False


def main():
    print("="*60)
    print("RATE LIMITING TEST SCRIPT")
    print("="*60)
    print()

    # Check backend health first
    if not check_backend_health():
        sys.exit(1)

    print()

    # Run the test
    num_requests = 12
    if len(sys.argv) > 1:
        try:
            num_requests = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number of requests: {sys.argv[1]}")
            sys.exit(1)

    success = test_rate_limiting(num_requests)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
