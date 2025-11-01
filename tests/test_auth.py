import pytest
import requests
import uuid
import os
import asyncio
import websockets
import json

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080")
WS_URL = f"ws://{BASE_URL.split('//')[1]}/ws" if BASE_URL.startswith("http") else f"ws://{BASE_URL}/ws"


@pytest.fixture
def unique_user_payload():
    """
    Pytest fixture to generate a unique user payload for registration.
    """
    unique_id = uuid.uuid4()
    return {
        "username": f"testuser_{unique_id}",
        "password": f"password_{unique_id}",
        "email": f"test_{unique_id}@example.com",
    }


def test_user_registration_success(unique_user_payload):
    """
    Tests successful user registration via HTTP.
    """
    response = requests.post(f"{BASE_URL}/register", json=unique_user_payload)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json["status"] == "success"
    assert response_json["message"] == "User registered successfully"


def test_user_registration_failure_duplicate_user(unique_user_payload):
    """
    Tests that registration fails if the user already exists via HTTP.
    """
    # First registration should succeed
    response1 = requests.post(f"{BASE_URL}/register", json=unique_user_payload)
    assert response1.status_code == 201

    # Second registration with the same data should fail
    response2 = requests.post(f"{BASE_URL}/register", json=unique_user_payload)
    assert response2.status_code == 409  # Conflict
    assert "Username or email already exists" in response2.text


@pytest.mark.asyncio
async def test_user_registration_and_authentication(unique_user_payload):
    """
    Tests that a user can be created and then authenticated via WebSocket.
    """
    # Register user via WebSocket to get a token
    async with websockets.connect(WS_URL) as websocket:
        register_payload = {
            "type": "register",
            "payload": unique_user_payload
        }
        await websocket.send(json.dumps(register_payload))
        
        response_str = await websocket.recv()
        response_data = json.loads(response_str)
        
        assert response_data.get("type") == "register_success"
        token = response_data.get("payload", {}).get("token")
        assert token is not None

    # Authenticate with the token in a new connection
    async with websockets.connect(WS_URL) as websocket:
        token_auth_payload = {
            "type": "token_auth",
            "payload": {"token": token},
        }
        await websocket.send(json.dumps(token_auth_payload))

        response_str = await websocket.recv()
        response_data = json.loads(response_str)

        assert response_data["type"] == "auth_success"
        assert "token" in response_data["payload"]
