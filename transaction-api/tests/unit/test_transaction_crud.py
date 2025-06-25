import datetime
import pytest
from app.crud import transaction
from app.schemas.transaction import TransactionCreate

def test_create_and_get_transaction(db_session):
    # Cria uma transação fake
    transaction_data = TransactionCreate(nome="Teste", mcc="1234", valor=150.0)
    processing_date = datetime.datetime.now()

    # Cria no DB
    created = transaction.create_db_transaction(db_session, transaction_data, processing_date)

    assert created.id is not None
    assert created.nome == transaction_data.nome
    assert created.mcc == transaction_data.mcc
    assert created.valor == transaction_data.valor
    assert created.data == processing_date

    # Busca pelo nome e valor
    found = transaction.get_transaction_by_name_and_value(db_session, "Teste", 150.0)
    assert found is not None
    assert found.id == created.id

def test_get_db_transactions(db_session):
    # Insere várias transações
    for i in range(5):
        t = TransactionCreate(nome=f"Nome{i}", mcc="1111", valor=100.0 + i)
        transaction.create_db_transaction(db_session, t, datetime.datetime.now())

    # Busca todas (limit default 100)
    txs = transaction.get_db_transactions(db_session)
    assert len(txs) == 5

    # Testa skip e limit
    txs_skip = transaction.get_db_transactions(db_session, skip=2, limit=2)
    assert len(txs_skip) == 2

def test_get_db_transactions_by_mcc(db_session):
    # Insere transações com diferentes MCC
    t1 = TransactionCreate(nome="A", mcc="1111", valor=50)
    t2 = TransactionCreate(nome="B", mcc="2222", valor=60)
    t3 = TransactionCreate(nome="C", mcc="1111", valor=70)

    transaction.create_db_transaction(db_session, t1, datetime.datetime.now())
    transaction.create_db_transaction(db_session, t2, datetime.datetime.now())
    transaction.create_db_transaction(db_session, t3, datetime.datetime.now())

    txs_1111 = transaction.get_db_transactions_by_mcc(db_session, "1111")
    assert len(txs_1111) == 2
    assert all(t.mcc == "1111" for t in txs_1111)

    txs_2222 = transaction.get_db_transactions_by_mcc(db_session, "2222")
    assert len(txs_2222) == 1
    assert txs_2222[0].nome == "B"
