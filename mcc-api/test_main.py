import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from faker import Faker
from main import app, MccEntry

fake = Faker()

def generate_fake_mcc_entry():
    return {
        "code": fake.unique.random_int(min=1000, max=9999),
        "description": fake.company()
    }

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def fake_mcc_data():
    # Gera uma lista de MCCs fake
    return [generate_fake_mcc_entry() for _ in range(5)]

@patch("main.load_mcc_data")
def test_get_all_mcc_codes(mock_load, client, fake_mcc_data):
    # Mocka o carregamento dos dados
    mock_load.return_value = [MccEntry(**item) for item in fake_mcc_data]
    # Força o carregamento dos dados no app
    with client:
        app.dependency_overrides = {}
        
        response = client.get("/mcc")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == len(fake_mcc_data)

@patch("main.load_mcc_data")
def test_get_mcc_by_code_found(mock_load, client, fake_mcc_data):
    mock_load.return_value = [MccEntry(**item) for item in fake_mcc_data]
    code = fake_mcc_data[0]["code"]
    with client:
        app.dependency_overrides = {}
        
        response = client.get(f"/mcc/{code}")
        assert response.status_code == 200
        assert response.json()["code"] == code

@patch("main.load_mcc_data")
def test_get_mcc_by_code_not_found(mock_load, client, fake_mcc_data):
    mock_load.return_value = [MccEntry(**item) for item in fake_mcc_data]
    code = 999999  # Um código que não existe
    with client:
        app.dependency_overrides = {}
        
        response = client.get(f"/mcc/{code}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()