"""
Simple test script for the FastAPI service.
Run this after starting the API server.
"""

import requests
import json

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("Testing /health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_generate():
    """Test text generation endpoint."""
    print("Testing /generate endpoint...")
    payload = {
        "prefix": "ایک بار",
        "max_length": 100,
        "temperature": 0.9,
        "random_seed": 42
    }
    response = requests.post(f"{API_URL}/generate", json=payload)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Generated text: {result['generated_text'][:200]}...")
        print(f"Tokens generated: {result['num_tokens']}")
        print(f"Stopped at EOT: {result['stopped_at_eot']}")
    else:
        print(f"Error: {response.text}")
    print()

if __name__ == "__main__":
    try:
        test_health()
        test_generate()
        print("✓ All tests passed!")
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to API. Make sure the server is running:")
        print("  python api.py")
    except Exception as e:
        print(f"✗ Error: {e}")
