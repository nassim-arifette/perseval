"""Script to export newsletter subscribers to CSV."""
import os
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5371")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

def export_subscribers_to_csv(output_file: str = None):
    """Export newsletter subscribers to a CSV file."""

    if not ADMIN_API_KEY:
        print("❌ Error: ADMIN_API_KEY not set in .env file")
        print("Add this line to your .env file:")
        print("ADMIN_API_KEY=your-secret-key-here")
        return

    # Default filename with timestamp
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"newsletter_subscribers_{timestamp}.csv"

    print(f"🔄 Fetching subscribers from {BACKEND_URL}...")

    try:
        response = requests.get(
            f"{BACKEND_URL}/admin/newsletter/subscribers",
            params={"api_key": ADMIN_API_KEY}
        )

        if response.status_code == 401:
            print("❌ Error: Invalid API key")
            return

        if response.status_code != 200:
            print(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
            return

        data = response.json()
        subscribers = data.get("subscribers", [])
        total = data.get("total", 0)

        if total == 0:
            print("ℹ️  No subscribers found")
            return

        print(f"✅ Found {total} subscribers")

        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if subscribers:
                fieldnames = subscribers[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(subscribers)

        print(f"📄 Exported to: {output_file}")
        print(f"\nSubscriber summary:")
        print(f"  - Total subscribers: {total}")

        # Show some stats if available
        if subscribers:
            avg_helpfulness = sum(s.get('helpfulness_rate', 0) for s in subscribers) / len(subscribers)
            print(f"  - Average helpfulness rate: {avg_helpfulness:.1%}")

    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to backend at {BACKEND_URL}")
        print("Make sure your backend is running: python -m uvicorn backend.main:app")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys

    output_file = sys.argv[1] if len(sys.argv) > 1 else None
    export_subscribers_to_csv(output_file)
