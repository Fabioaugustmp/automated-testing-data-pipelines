# app/api/endpoints/transaction.py
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.db.session import get_db
from app.crud.transaction import get_db_transactions, get_db_transactions_by_mcc
from app.etl.processor import process_and_load_transaction
from app.etl.processor import process_and_create_transaction_with_mcc_request

router = APIRouter(
    prefix="/transacoes",
    tags=["Transações"]
)

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_transacao(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    Endpoint para cadastrar uma nova transação.

    - **nome**: Nome do estabelecimento.
    - **mcc**: Código de Categoria do Comerciante.
    - **valor**: Valor da transação.
    """
    created_transaction = process_and_load_transaction(db, transaction)
    return created_transaction

@router.post("/with-mcc", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def cadastrar_transacao_mcc(
        transaction: TransactionCreate,
        db: Session = Depends(get_db)
):
    created_transaction = await process_and_create_transaction_with_mcc_request(db, transaction)
    return created_transaction


@router.get("/", response_model=List[TransactionResponse])
def consultar_transacoes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Endpoint para consultar todas as transações cadastradas com paginação.
    """
    transactions = get_db_transactions(db, skip=skip, limit=limit)
    return transactions

@router.get("/mcc", response_model=List[TransactionResponse], tags=["MCC"])
def consultar_por_mcc(
        mcc: str,
        db: Session = Depends(get_db)
):
    """
    Endpoint para consultar transações por Código de Categoria do Comerciante (MCC).
    """
    transactions = get_db_transactions_by_mcc(db, mcc)
    return transactions