# app/etl/processor.py
import datetime
import httpx
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.crud.transaction import get_transaction_by_name_and_value, create_db_transaction

client = httpx.AsyncClient()
logger = logging.getLogger(__name__)

def process_and_load_transaction(db: Session, transaction_data: TransactionCreate) -> TransactionResponse:
    """
    Simple ETL Process:
    1. Extract: Data is extracted from the API request (transaction_data).
    2. Transform: Data is validated (here, checking for duplicates) and processing date is added.
    3. Load: Transformed data is loaded into the database.
    """
    # Example of transformation/validation rule: do not allow identical transactions (same name and value)
    existing_transaction = get_transaction_by_name_and_value(db, nome=transaction_data.nome, valor=transaction_data.valor)
    if existing_transaction:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uma transação similar já foi registrada."
        )

    # Add processing date (timestamp)
    processing_date = datetime.datetime.now()

    # Load data into the database
    created_transaction = create_db_transaction(db=db, transaction=transaction_data, processing_date=processing_date)
    return created_transaction

async def call_mcc_api(mcc):
    try:
     response = await client.get(f"http://127.0.0.1:8001/mcc/{mcc}")
     response.raise_for_status()
     data = response.json()
     return data
    except httpx.HTTPStatusError as exc:
     return {"error": f"HTTP error {exc.response.status_code}"}
    except httpx.RequestError as exc:
        return {"error": f"An error occurred during request: {exc}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}

async def process_and_create_transaction_with_mcc_request(db: Session, transaction_data: TransactionCreate) -> TransactionResponse:

    mcc_response = await call_mcc_api(mcc=transaction_data.mcc)
    if "error" in mcc_response:
        logger.warning(f"MCC inválido ou erro na chamada externa: {mcc_response['error']}")
        raise HTTPException(status_code=400, detail=f"Erro ao buscar MCC: {transaction_data.mcc}, inválido ou erro na chamada externa {mcc_response['error']}")

    logger.info(f"MCC encontrado com sucesso: {mcc_response}")

    return process_and_load_transaction(db, transaction_data)
