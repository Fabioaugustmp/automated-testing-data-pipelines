# app/crud/transaction.py
import datetime
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate

def get_transaction_by_name_and_value(db: Session, nome: str, valor: float):
    """Busca uma transação específica para evitar duplicatas simples."""
    return db.query(Transaction).filter(Transaction.nome == nome, Transaction.valor == valor).first()

def create_db_transaction(db: Session, transaction: TransactionCreate, processing_date: datetime.datetime):
    """Cria e salva uma nova transação no banco de dados."""
    db_transaction = Transaction(
        nome=transaction.nome,
        mcc=transaction.mcc,
        valor=transaction.valor,
        data=processing_date
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_db_transactions(db: Session, skip: int = 0, limit: int = 100):
    """Retorna uma lista de transações do banco de dados."""
    return db.query(Transaction).offset(skip).limit(limit).all()

def get_db_transactions_by_mcc(db: Session, mcc: str):
    return db.query(Transaction).filter(Transaction.mcc == mcc).all()