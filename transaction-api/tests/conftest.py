import os
import sys
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.main import app
from app.db.session import get_db

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

#Tipo de Testes Fixtures e dependências

# DB de testes em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Substitui o get_db do FastAPI por um banco de teste
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Criação de tabelas
Base.metadata.create_all(bind=engine)
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    yield TestClient(app)
