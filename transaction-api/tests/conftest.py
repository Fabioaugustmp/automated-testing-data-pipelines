# transaction-api/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. IMPORTAÇÃO ABSOLUTA (A FORMA CORRETA)
# Isso diz ao Python para procurar o pacote 'app' a partir da raiz do projeto.
from app.main import app
from app.db.session import get_db
from app.db.base import Base

# --- Configuração do Banco de Dados de Teste ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

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