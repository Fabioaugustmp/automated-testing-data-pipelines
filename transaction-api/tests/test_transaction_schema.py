from app.schemas.transaction import TransactionCreate
from pydantic import ValidationError
import pytest

def test_valid_transaction_schema():
    data = {
        "nome": "Loja Teste",
        "mcc": "1234",
        "valor": 99.99
    }
    trans = TransactionCreate(**data)
    assert trans.nome == "Loja Teste"

def test_invalid_transaction_schema():
    data = {
        "nome": "Teste",
        "mcc": None,
        "valor": "errado"
    }
    with pytest.raises(ValidationError):
        TransactionCreate(**data)
