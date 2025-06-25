# transaction-api/tests/conftest.py

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

# 1. IMPORTAÇÃO ABSOLUTA (A FORMA CORRETA)
# Isso diz ao Python para procurar o pacote 'app' a partir da raiz do projeto.
from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.crud import transaction

# --- Configuração do Banco de Dados de Teste ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Remove o arquivo de banco de dados de teste, se existir
if os.path.exists("test.db"):
    os.remove("test.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Criação das Tabelas ---
# Garante que todas as tabelas sejam criadas no banco de memória antes dos testes.
Base.metadata.create_all(bind=engine)


# --- Substituição da Dependência do Banco de Dados ---
def override_get_db():
    """
    Substitui a dependência get_db para usar o banco de dados de teste em memória
    durante a execução dos testes.
    """
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()

# Aplica a substituição na instância do app do FastAPI
app.dependency_overrides[get_db] = override_get_db


# --- Fixture do Cliente de Teste ---
@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    Cria um cliente de teste que pode fazer requisições à nossa aplicação
    em memória.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_transactions_table(db_session):
    """Limpa a tabela de transações antes de cada teste unitário."""
    db_session.query(transaction.Transaction).delete()
    db_session.commit()