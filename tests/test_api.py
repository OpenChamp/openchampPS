import requests
import os

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080")


def test_health_check():
    """
    Tests if the /health endpoint is working.
    """
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.text == "OK"
