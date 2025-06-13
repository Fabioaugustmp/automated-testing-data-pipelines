# main.py
# --- Imports ---
import datetime
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

# --- Configuração do Banco de Dados (usando SQLite em arquivo) ---
# Em uma aplicação real, considere usar variáveis de ambiente para a URL.
SQLALCHEMY_DATABASE_URL = "sqlite:///./transactions.db"

# create_engine é o ponto de entrada para o banco de dados.
# O argumento connect_args é necessário apenas para SQLite para permitir o uso em múltiplos threads.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Cada instância de SessionLocal será uma sessão de banco de dados.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base será usada para criar os modelos do banco de dados (ORM).
Base = declarative_base()


# --- Modelos do Banco de Dados (SQLAlchemy ORM) ---
# Esta seção define como a tabela 'transactions' será no banco de dados.
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    mcc = Column(String, index=True)  # Merchant Category Code
    valor = Column(Float)
    data = Column(DateTime)


# --- Schemas (Pydantic) ---
# Esta seção define a estrutura dos dados para a API (validação de requests/responses).
class TransactionBase(BaseModel):
    nome: str = Field(..., example="Restaurante Comida Boa")
    mcc: str = Field(..., example="5812")
    valor: float = Field(..., gt=0, example=99.90)

# Schema para a criação de uma nova transação (entrada da API)
class TransactionCreate(TransactionBase):
    pass

# Schema para a leitura de uma transação (saída da API)
class TransactionResponse(TransactionBase):
    id: int
    data: datetime.datetime

    class Config:
        # Permite que o Pydantic leia dados de modelos ORM.
        orm_mode = True


# --- CRUD (Create, Read, Update, Delete) ---
# Funções que interagem diretamente com o banco de dados.
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

def get_db_transactions_by_mcc(db: Session, mcc):
    return db.query(Transaction).filter(Transaction.mcc == mcc).all()

# --- Lógica de ETL (Extract, Transform, Load) ---
# Função que centraliza o fluxo de processamento.
def process_and_load_transaction(db: Session, transaction_data: TransactionCreate):
    """
    Processo ETL simples:
    1. Extract: Os dados são extraídos do request da API (transaction_data).
    2. Transform: Validamos os dados (aqui, verificamos duplicatas) e adicionamos a data de processamento.
    3. Load: Carregamos os dados transformados no banco de dados.
    """
    # Exemplo de regra de transformação/validação: não permitir transações idênticas (mesmo nome e valor)
    existing_transaction = get_transaction_by_name_and_value(db, nome=transaction_data.nome, valor=transaction_data.valor)
    if existing_transaction:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uma transação similar já foi registrada."
        )

    # Adiciona a data de processamento (timestamp)
    processing_date = datetime.datetime.now()

    # Carga (Load) dos dados no banco
    return create_db_transaction(db=db, transaction=transaction_data, processing_date=processing_date)


# --- Configuração do FastAPI ---
app = FastAPI(
    title="API de Transações com ETL",
    description="Uma API simples para registrar e consultar transações financeiras usando um fluxo ETL.",
    version="1.0.0"
)

# Cria as tabelas no banco de dados na inicialização da API (se não existirem).
# Em ambientes de produção, use ferramentas de migração como Alembic.
Base.metadata.create_all(bind=engine)

# --- Dependência para Sessão do Banco de Dados ---
def get_db():
    """
    Esta função é uma dependência do FastAPI. Ela cria uma sessão de banco de dados por request,
    garantindo que a sessão seja fechada corretamente após o uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Endpoints da API ---
@app.post("/transacoes/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, tags=["Transações"])
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
    # Chama o fluxo ETL para processar e salvar a transação
    created_transaction = process_and_load_transaction(db, transaction)
    return created_transaction

@app.get("/transacoes/", response_model=List[TransactionResponse], tags=["Transações"])
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

@app.get("/transacoes/mcc", response_model=List[TransactionResponse], tags=["MCC"])
def consultar_por_mcc(
        mcc,
        db: Session = Depends(get_db)
):
    transactions = get_db_transactions_by_mcc(db, mcc)
    return transactions