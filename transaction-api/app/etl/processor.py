# app/etl/processor.py
import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.crud.transaction import get_transaction_by_name_and_value, create_db_transaction

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