"""Test script for the simplified feedback endpoint."""
import requests

# Backend URL (adjust if needed)
BASE_URL = "http://localhost:5371"

def test_feedback():
    """Test submitting user feedback with emoji ratings."""

    feedback_data = {
        "analysis_type": "full",
        "analyzed_entity": "@test_influencer",
        "experience_rating": "good",  # 'good', 'medium', or 'bad'
        "review_text": "This analysis was very helpful and detailed!",
        "email": "test@example.com",
        "email_consented": True
    }

    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": "test-session-123"
    }

    print("Submitting feedback with 'good' rating...")
    response = requests.post(
        f"{BASE_URL}/feedback",
        json=feedback_data,
        headers=headers
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        print("✅ Feedback submitted successfully!")
    else:
        print("❌ Failed to submit feedback")

def test_all_ratings():
    """Test all three emoji ratings."""

    ratings = [
        ("good", "Great experience! Very helpful."),
        ("medium", "It was okay, could be better."),
        ("bad", "Not helpful at all.")
    ]

    for rating, review in ratings:
        print(f"\n📝 Testing '{rating}' rating...")

        feedback_data = {
            "analysis_type": "full",
            "experience_rating": rating,
            "review_text": review
        }

        response = requests.post(
            f"{BASE_URL}/feedback",
            json=feedback_data,
            headers={"X-Session-ID": f"test-session-{rating}"}
        )

        if response.status_code == 200:
            print(f"✅ {rating.upper()} rating submitted")
        else:
            print(f"❌ Failed: {response.json()}")

def test_rate_limiting():
    """Test rate limiting by submitting multiple feedbacks."""

    print("\n🔒 Testing rate limiting (submitting 4 feedbacks rapidly)...")

    for i in range(4):
        feedback_data = {
            "analysis_type": "full",
            "experience_rating": "good",
            "review_text": f"Test feedback #{i+1}"
        }

        response = requests.post(
            f"{BASE_URL}/feedback",
            json=feedback_data,
            headers={"X-Session-ID": "test-session-rate-limit"}
        )

        print(f"Attempt {i+1}: Status {response.status_code}")

        if response.status_code == 429:
            print("✅ Rate limiting is working!")
            break

def test_validation():
    """Test input validation."""

    print("\n🛡️ Testing validation...")

    # Test missing required field
    print("\n1. Testing missing experience_rating...")
    response = requests.post(
        f"{BASE_URL}/feedback",
        json={
            "analysis_type": "full",
            "review_text": "Test"
        },
        headers={"X-Session-ID": "test-validation"}
    )
    print(f"   Status: {response.status_code} - {'✅ Rejected' if response.status_code == 422 else '❌ Should reject'}")

    # Test invalid rating
    print("\n2. Testing invalid experience_rating...")
    response = requests.post(
        f"{BASE_URL}/feedback",
        json={
            "analysis_type": "full",
            "experience_rating": "invalid",
            "review_text": "Test"
        },
        headers={"X-Session-ID": "test-validation"}
    )
    print(f"   Status: {response.status_code} - {'✅ Rejected' if response.status_code == 422 else '❌ Should reject'}")

    # Test XSS attempt
    print("\n3. Testing XSS prevention...")
    response = requests.post(
        f"{BASE_URL}/feedback",
        json={
            "analysis_type": "full",
            "experience_rating": "good",
            "review_text": "<script>alert('xss')</script>"
        },
        headers={"X-Session-ID": "test-validation"}
    )
    print(f"   Status: {response.status_code} - {'✅ Blocked' if response.status_code == 422 else '❌ Should block'}")

if __name__ == "__main__":
    print("=" * 60)
    print("FEEDBACK SYSTEM TEST SUITE")
    print("=" * 60)

    # Test basic feedback submission
    test_feedback()

    # Test all three ratings
    test_all_ratings()

    # Test validation
    test_validation()

    # Test rate limiting (run last as it might block)
    test_rate_limiting()

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
