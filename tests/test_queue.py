import requests
import pytest
import uuid
import os
import asyncio
import websockets
import json

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8080")
WS_URL = f"ws://{BASE_URL.split('//')[1]}/ws" if BASE_URL.startswith("http") else f"ws://{BASE_URL}/ws"


async def register_and_get_token(username, password, email):
    """Helper function to register a user via WebSocket and get a token."""
    async with websockets.connect(WS_URL, open_timeout=30) as websocket:
        payload = {"username": username, "password": password, "email": email}
        await websocket.send(json.dumps({"type": "register", "payload": payload}))
        
        response = await asyncio.wait_for(websocket.recv(), timeout=30)
        data = json.loads(response)
        
        assert data["type"] == "register_success"
        assert "token" in data["payload"]
        return data["payload"]["token"]


async def player_flow(token):
    """Simulates a player connecting, logging in, and joining the queue."""
    # Increased connection timeout
    async with websockets.connect(WS_URL, open_timeout=30) as websocket:
        # Login with token
        await websocket.send(json.dumps({"type": "token_auth", "payload": {"token": token}}))
        
        # Increased receive timeout
        login_response = await asyncio.wait_for(websocket.recv(), timeout=30)
        login_data = json.loads(login_response)
        assert login_data["type"] == "auth_success"
        
        # Join queue
        await websocket.send(json.dumps({"type": "join_queue"}))
        
        # Increased receive timeout
        queue_response = await asyncio.wait_for(websocket.recv(), timeout=30)
        assert json.loads(queue_response) == {"type": "queued"}
        
        # Wait for match
        # Increased timeout for match response
        match_response = await asyncio.wait_for(websocket.recv(), timeout=40) 
        match_data = json.loads(match_response)
        assert match_data["type"] == "match_found", \
    f"Expected match_found, got {match_data.get('type')}. Full payload: {match_data}"
        return match_data

@pytest.mark.asyncio
async def test_queue_and_match():
    """
    Tests queuing two players and verifying they get matched.
    """
    # Generate unique users
    uid1 = uuid.uuid4()
    user1_username = f"testuser_{uid1}"
    user1_password = f"password_{uid1}"
    user1_email = f"test_{uid1}@example.com"

    uid2 = uuid.uuid4()
    user2_username = f"testuser_{uid2}"
    user2_password = f"password_{uid2}"
    user2_email = f"test_{uid2}@example.com"
    
    # Register users via WebSocket and get tokens
    token1 = await register_and_get_token(user1_username, user1_password, user1_email)
    token2 = await register_and_get_token(user2_username, user2_password, user2_email)

    # Run player flows concurrently
    task1 = asyncio.create_task(player_flow(token1))
    await asyncio.sleep(1) # a small delay to ensure player 1 joins queue first this is set too high TODO fix
    task2 = asyncio.create_task(player_flow(token2))
    
    match_data1, match_data2 = await asyncio.gather(task1, task2)

    # Verify match details
    # Note: Since the server doesn't tell us our own username back on match,
    # we can't easily assert the opponent's name without more complex state tracking.

    assert "players" in match_data1["payload"]
    assert "players" in match_data2["payload"]
    assert match_data1["payload"]["port"] == match_data2["payload"]["port"]
    assert "containerID" in match_data1["payload"]
    assert "containerID" in match_data2["payload"]

    # Check that the players in the match are the correct ones
    expected_players = {user1_username, user2_username}
    assert set(match_data1["payload"]["players"]) == expected_players
    assert set(match_data2["payload"]["players"]) == expected_players
