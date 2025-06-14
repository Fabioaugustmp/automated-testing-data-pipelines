# test_transactions.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime

from fastapi import HTTPException, status
from hypothesis import given, strategies as st
from sqlalchemy.orm import Session

# Import functions and classes from your main.py
from main import (
    Transaction,
    TransactionCreate,
    process_and_load_transaction,
    get_db_transactions_by_mcc,
    get_db_transactions,
    create_db_transaction,
    get_transaction_by_name_and_value
)

# --- Hypothesis Strategies ---
# Define strategies for generating valid transaction data
transaction_name_st = st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=['Cs', 'Cc', 'Cf', 'Co', 'Cn']))
mcc_st = st.text(min_size=4, max_size=4, alphabet="0123456789") # MCCs are typically 4 digits
value_st = st.floats(min_value=0.01, max_value=10000.00, allow_nan=False, allow_infinity=False, exclude_min=True)

@st.composite
def transaction_create_strategy(draw):
    """Strategy to generate valid TransactionCreate instances."""
    return TransactionCreate(
        nome=draw(transaction_name_st),
        mcc=draw(mcc_st),
        valor=draw(value_st)
    )

# --- Fixtures for Mocking ---
@pytest.fixture
def mock_db_session(mocker):
    """Fixture to provide a mocked SQLAlchemy Session."""
    mock_session = mocker.MagicMock(spec=Session)
    mock_session.query.return_value.filter.return_value.first.return_value = None # Default: no existing transaction
    mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [] # Default: no transactions
    return mock_session

# --- Hypothesis Tests ---

## Testing process_and_load_transaction

@given(transaction_data=transaction_create_strategy())
def test_process_and_load_transaction_success(mock_db_session, transaction_data):
    """
    Hypothesis: Given valid transaction data and no existing duplicates,
    process_and_load_transaction should successfully create a new transaction.
    """
    # Mock create_db_transaction to return a mock Transaction instance
    mock_transaction = Transaction(
        id=1,
        nome=transaction_data.nome,
        mcc=transaction_data.mcc,
        valor=transaction_data.valor,
        data=datetime.now()
    )
    mock_db_session.add.return_value = None # Mock add
    mock_db_session.commit.return_value = None # Mock commit
    mock_db_session.refresh.side_effect = lambda x: x # Mock refresh to update the object in place

    # We need to mock get_transaction_by_name_and_value directly
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    # Manually call create_db_transaction within the test to mock it effectively
    # This ensures that process_and_load_transaction calls this mocked version
    with (
        mocker.patch('main.create_db_transaction', return_value=mock_transaction) as mock_create_db_transaction,
        mocker.patch('main.get_transaction_by_name_and_value', return_value=None) as mock_get_transaction_by_name_and_value
    ):
        result_transaction = process_and_load_transaction(mock_db_session, transaction_data)

        mock_get_transaction_by_name_and_value.assert_called_once_with(mock_db_session, nome=transaction_data.nome, valor=transaction_data.valor)
        mock_create_db_transaction.assert_called_once() # We don't check args strictly here as it's mocked internal

        assert result_transaction is not None
        assert result_transaction.nome == transaction_data.nome
        assert result_transaction.mcc == transaction_data.mcc
        assert result_transaction.valor == transaction_data.valor
        assert isinstance(result_transaction.data, datetime)


@given(transaction_data=transaction_create_strategy())
def test_process_and_load_transaction_duplicate_conflict(mock_db_session, transaction_data):
    """
    Hypothesis: Given transaction data that is considered a duplicate,
    process_and_load_transaction should raise an HTTPException with 409 CONFLICT.
    """
    # Simulate an existing transaction being found
    existing_transaction = Transaction(
        id=1,
        nome=transaction_data.nome,
        mcc=transaction_data.mcc,
        valor=transaction_data.valor,
        data=datetime.now()
    )
    # Mock get_transaction_by_name_and_value to return the existing transaction
    with mocker.patch('main.get_transaction_by_name_and_value', return_value=existing_transaction) as mock_get_existing:
        with pytest.raises(HTTPException) as exc_info:
            process_and_load_transaction(mock_db_session, transaction_data)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "Uma transação similar já foi registrada." in exc_info.value.detail
        mock_get_existing.assert_called_once_with(mock_db_session, nome=transaction_data.nome, valor=transaction_data.valor)


## Testing get_db_transactions_by_mcc

@given(
    mcc_to_filter=mcc_st,
    all_transactions_data=st.lists(transaction_create_strategy(), min_size=1, max_size=20)
)
def test_get_db_transactions_by_mcc(mock_db_session, mcc_to_filter, all_transactions_data):
    """
    Hypothesis: When filtering transactions by MCC, only transactions matching that MCC should be returned.
    """
    # Convert generated TransactionCreate data to mock Transaction objects
    mock_db_transactions = []
    for i, data in enumerate(all_transactions_data):
        mock_db_transactions.append(
            Transaction(
                id=i + 1,
                nome=data.nome,
                mcc=data.mcc,
                valor=data.valor,
                data=datetime.now()
            )
        )

    # Configure the mock session to return our list of transactions
    # We mock the entire query chain to filter by MCC
    class MockQuery:
        def __init__(self, transactions):
            self.transactions = transactions

        def filter(self, *args):
            # This is a simplified mock of filter.
            # In a real scenario, you might parse args to simulate SQL filtering more accurately.
            # Here, we're assuming the filter is on Transaction.mcc == mcc_to_filter
            return self

        def all(self):
            # Simulate the filtering based on mcc_to_filter
            return [t for t in self.transactions if t.mcc == mcc_to_filter]

    mock_db_session.query.return_value = MockQuery(mock_db_transactions)

    # Call the function under test
    result_transactions = get_db_transactions_by_mcc(mock_db_session, mcc_to_filter)

    # Assertions
    for transaction in result_transactions:
        assert transaction.mcc == mcc_to_filter

    # Verify that the correct number of transactions were returned
    expected_count = sum(1 for t in mock_db_transactions if t.mcc == mcc_to_filter)
    assert len(result_transactions) == expected_count


## Testing get_db_transactions (pagination)

@given(
    skip=st.integers(min_value=0, max_value=10),
    limit=st.integers(min_value=1, max_value=10),
    num_transactions=st.integers(min_value=0, max_value=20)
)
def test_get_db_transactions_pagination(mock_db_session, skip, limit, num_transactions):
    """
    Hypothesis: get_db_transactions should correctly apply skip and limit for pagination.
    """
    # Generate a list of mock transactions
    mock_all_transactions = []
    for i in range(num_transactions):
        mock_all_transactions.append(
            Transaction(
                id=i + 1,
                nome=f"Txn {i}",
                mcc="1234",
                valor=10.0 + i,
                data=datetime.now()
            )
        )

    # Mock the SQLAlchemy query chain for offset and limit
    class MockQueryForPagination:
        def __init__(self, transactions_data):
            self.transactions_data = transactions_data

        def offset(self, skip_val):
            self._offset = skip_val
            return self

        def limit(self, limit_val):
            self._limit = limit_val
            return self

        def all(self):
            start = self._offset
            end = self._offset + self._limit
            return self.transactions_data[start:end]

    mock_db_session.query.return_value = MockQueryForPagination(mock_all_transactions)

    # Call the function under test
    result_transactions = get_db_transactions(mock_db_session, skip=skip, limit=limit)

    # Expected transactions based on skip and limit
    expected_transactions = mock_all_transactions[skip:skip + limit]

    assert len(result_transactions) == len(expected_transactions)
    assert result_transactions == expected_transactions