import pytest
from faker import Faker
from unittest.mock import AsyncMock, patch
from app.schemas.transaction import TransactionCreate

# Testes dos Endpoints

fake = Faker()

def test_post_transaction(client):
    payload = {
        "nome": fake.company(),
        "mcc": "1234",
        "valor": fake.dollar()
    }
    response = client.post("/transacoes/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["mcc"] == payload["mcc"]
    assert data["valor"] == payload["valor"]

def test_get_transactions(client):
    response = client.get("/transacoes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_transactions_by_mcc(client):
    mcc = "1234"
    response = client.get(f"/transacoes/mcc?mcc={mcc}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
@patch("app.etl.processor.call_mcc_api", new_callable=AsyncMock)
async def test_post_transaction_with_mcc(mock_call_mcc, client):
    mock_call_mcc.return_value = {"valid": True}

    payload = {
        "nome": fake.company(),
        "mcc": "5678",
        "valor": 200.00
    }

    async with client:
        response = await client.post("/transacoes/with-mcc", json=payload)
        assert response.status_code == 201