# test_main.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app, Base, get_db, TransactionCreate, process_and_load_transaction
from fastapi import HTTPException

# --- Configuração do banco de dados em memória para testes ---
SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool  # Importante para testes em memória
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Criar as tabelas no banco de testes
Base.metadata.create_all(bind=engine)

# --- Fixture para injetar o DB de teste na API ---
@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


# --- Testes de Integração ---

def test_create_transaction(client):
    payload = {
        "nome": "Loja do Zé",
        "mcc": "5411",
        "valor": 59.99
    }
    response = client.post("/transacoes/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == payload["nome"]
    assert data["mcc"] == payload["mcc"]
    assert data["valor"] == payload["valor"]
    assert "id" in data
    assert "data" in data

def test_get_transactions(client):
    response = client.get("/transacoes/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # Deve conter ao menos o criado anteriormente

def test_duplicate_transaction(client):
    payload = {
        "nome": "Posto Shell",
        "mcc": "5541",
        "valor": 100.00
    }

    # Primeira inserção
    response1 = client.post("/transacoes/", json=payload)
    assert response1.status_code == 201

    # Segunda inserção duplicada
    response2 = client.post("/transacoes/", json=payload)
    assert response2.status_code == 409
    assert response2.json()["detail"] == "Uma transação similar já foi registrada."


# --- Testes de Validação ---

def test_invalid_transaction_value(client):
    payload = {
        "nome": "Mercado XYZ",
        "mcc": "5411",
        "valor": -5.00
    }
    response = client.post("/transacoes/", json=payload)
    assert response.status_code == 422  # Unprocessable Entity

def test_missing_field(client):
    payload = {
        "nome": "Sem MCC",
        "valor": 50.00
    }
    response = client.post("/transacoes/", json=payload)
    assert response.status_code == 422


# --- Teste Unitário: ETL sem API ---

def test_process_and_load_transaction_etl():
    # Setup: criar sessão e entrada
    db = TestingSessionLocal()
    tx_data = TransactionCreate(nome="Bar do João", mcc="5813", valor=88.80)

    # Execução do fluxo ETL
    created = process_and_load_transaction(db, tx_data)

    # Verificação
    assert created.nome == tx_data.nome
    assert created.mcc == tx_data.mcc
    assert created.valor == tx_data.valor
    assert created.data is not None

    # Cleanup
    db.close()

def test_etl_duplicate_check():
    db = TestingSessionLocal()
    tx_data = TransactionCreate(nome="Farmácia Popular", mcc="5912", valor=25.00)

    # Inserção válida
    process_and_load_transaction(db, tx_data)

    # Tentativa duplicada
    with pytest.raises(HTTPException) as e:
        process_and_load_transaction(db, tx_data)
    assert e.value.status_code == 409

    db.close()


