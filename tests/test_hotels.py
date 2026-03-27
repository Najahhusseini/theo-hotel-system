# tests/test_hotels.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_hotel():
    """Test hotel creation"""
    # Login first
    login_response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "Admin123!"
    })
    token = login_response.json()["access_token"]
    
    # Create hotel
    response = client.post(
        "/api/v1/hotels/",
        params={
            "name": "Test Hotel",
            "address": "123 Test St",
            "phone": "555-1234",
            "email": "test@hotel.com"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert "hotel" in response.json()