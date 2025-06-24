import datetime
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from faker import Faker
from hypothesis import given, strategies as st

from fastapi import HTTPException

from app.etl import processor
from app.schemas.transaction import TransactionCreate

fake = Faker()


# Fixture para criar dados TransactionCreate fake
@pytest.fixture
def fake_transaction_data():
    return TransactionCreate(
        nome=fake.name(),
        mcc=fake.pystr(min_chars=4, max_chars=4),  # MCC geralmente tem 4 dígitos
        valor=fake.pyfloat(left_digits=3, right_digits=2, positive=True)
    )


# Mock Session do SQLAlchemy
@pytest.fixture
def mock_db_session():
    return MagicMock()


# --- Testa process_and_load_transaction ---

@given(
    nome=st.text(min_size=1),
    valor=st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
    mcc=st.text(min_size=4, max_size=4)
)
def test_process_and_load_transaction_creates_new_transaction(nome, valor, mcc, mock_db_session):
    transaction_data = TransactionCreate(nome=nome, mcc=mcc, valor=valor)

    # Mocka get_transaction_by_name_and_value para retornar None (não duplicado)
    with patch('app.etl.processor.get_transaction_by_name_and_value', return_value=None) as mock_get, \
            patch('app.etl.processor.create_db_transaction') as mock_create:
        mock_create.return_value = 'transaction_created'

        result = processor.process_and_load_transaction(mock_db_session, transaction_data)

        mock_get.assert_called_once_with(mock_db_session, nome=nome, valor=valor)
        mock_create.assert_called_once()
        assert result == 'transaction_created'


def test_process_and_load_transaction_raises_conflict(fake_transaction_data, mock_db_session):
    # Simula que a transação já existe
    with patch('app.etl.processor.get_transaction_by_name_and_value', return_value='exists'):
        with pytest.raises(HTTPException) as exc_info:
            processor.process_and_load_transaction(mock_db_session, fake_transaction_data)

        assert exc_info.value.status_code == 409
        assert "já foi registrada" in exc_info.value.detail


# --- Testa call_mcc_api async ---

@pytest.mark.asyncio
async def test_call_mcc_api_success():
    fake_response = {"mcc": "1234", "description": "Test MCC"}

    async def mock_get(url):
        class MockResp:
            def raise_for_status(self):
                pass

            def json(self):
                return fake_response

        return MockResp()

    with patch('app.etl.processor.client.get', new=mock_get):
        response = await processor.call_mcc_api("1234")
        assert response == fake_response


@pytest.mark.asyncio
async def test_call_mcc_api_http_error():
    async def mock_get(url):
        class MockResp:
            status_code = 404

            def raise_for_status(self):
                raise processor.httpx.HTTPStatusError("Not Found", request=None, response=self)

        return MockResp()

    with patch('app.etl.processor.client.get', new=mock_get):
        response = await processor.call_mcc_api("9999")
        assert "error" in response
        assert "HTTP error 404" in response["error"]


@pytest.mark.asyncio
async def test_call_mcc_api_request_error():
    async def mock_get(url):
        raise processor.httpx.RequestError("Network error", request=None)

    with patch('app.etl.processor.client.get', new=mock_get):
        response = await processor.call_mcc_api("9999")
        assert "error" in response
        assert "An error occurred during request" in response["error"]


@pytest.mark.asyncio
async def test_call_mcc_api_unexpected_error():
    async def mock_get(url):
        raise Exception("Unexpected error")

    with patch('app.etl.processor.client.get', new=mock_get):
        response = await processor.call_mcc_api("9999")
        assert "error" in response
        assert "An unexpected error occurred" in response["error"]


# --- Testa process_and_create_transaction_with_mcc_request async ---

@pytest.mark.asyncio
async def test_process_and_create_transaction_with_mcc_request_success(fake_transaction_data, mock_db_session):
    fake_mcc_response = {"mcc": fake_transaction_data.mcc, "description": "Valid MCC"}

    # Mocka call_mcc_api para retornar sucesso
    with patch('app.etl.processor.call_mcc_api', new=AsyncMock(return_value=fake_mcc_response)) as mock_call_mcc, \
            patch('app.etl.processor.process_and_load_transaction',
                  return_value="created_transaction") as mock_process_load:
        result = await processor.process_and_create_transaction_with_mcc_request(mock_db_session, fake_transaction_data)
        mock_call_mcc.assert_awaited_once_with(fake_transaction_data.mcc)
        mock_process_load.assert_called_once_with(mock_db_session, fake_transaction_data)
        assert result == "created_transaction"


@pytest.mark.asyncio
async def test_process_and_create_transaction_with_mcc_request_mcc_error(fake_transaction_data, mock_db_session):
    # Mocka call_mcc_api para retornar erro
    with patch('app.etl.processor.call_mcc_api', new=AsyncMock(return_value={"error": "Not found"})):
        with pytest.raises(HTTPException) as exc_info:
            await processor.process_and_create_transaction_with_mcc_request(mock_db_session, fake_transaction_data)
        assert exc_info.value.status_code == 400
        assert "Erro ao buscar MCC" in exc_info.value.detail
