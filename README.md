# Automated Testing Data Pipelines - Transaction API

## Overview

This project is a **FastAPI** application designed to manage financial transactions with an ETL (Extract, Transform, Load) workflow. It provides endpoints to register, validate, and query transactions, including integration with an external MCC (Merchant Category Code) API for additional data enrichment.

The application uses **SQLAlchemy** for ORM/database access, **Pydantic** for data validation, and is fully tested with **pytest** and **hypothesis** for property-based testing. The project is structured for maintainability and extensibility, supporting both unit and integration tests.

---

## Features

- **Register Transactions:** Create new transactions with validation to prevent duplicates.
- **Query Transactions:** List all transactions or filter by MCC.
- **ETL Workflow:** Each transaction goes through extraction, transformation (validation, enrichment), and loading into the database.
- **External MCC API Integration:** Optionally enrich transactions with MCC data from an external service.
- **Comprehensive Testing:** Includes property-based, schema, and CRUD tests.

---

## Main Projects

### 1. Transaction API (`transaction-api/`)

#### Purpose

A FastAPI application for registering, validating, and querying financial transactions. It features:

- **ETL Workflow:** Each transaction is extracted from the request, validated and enriched (optionally via an external MCC API), and loaded into the database.
- **External API Integration:** Supports enrichment of transactions with Merchant Category Code (MCC) data from an external service.
- **Database Management:** Uses SQLAlchemy ORM for database operations and Pydantic for data validation.
- **Comprehensive Testing:** Includes unit, integration, and property-based tests.

#### Structure

```
transaction-api/
│
├── app/
│   ├── api/           # FastAPI endpoints
│   ├── core/          # App configuration
│   ├── crud/          # Database CRUD operations
│   ├── db/            # Database setup and session
│   ├── etl/           # ETL processing logic
│   ├── models/        # SQLAlchemy models
│   └── schemas/       # Pydantic schemas
│
├── tests/
│   ├── unit/          # Unit tests for internal logic
│   ├── conftest.py    # Pytest fixtures and setup
│   ├── test_transaction_hyp_routes.py  # Hypothesis property-based API tests
│   ├── test_transaction_routes.py      # Standard API endpoint tests
│   └── test_transaction_schema.py      # Pydantic schema validation tests
│
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

---

## Tests Overview

### `tests/conftest.py`

**Purpose:**  
Sets up the testing environment for all tests.  
- Creates a fresh SQLite test database.
- Overrides FastAPI dependencies to use the test DB.
- Provides fixtures for the test client and database session.
- Cleans the transactions table before each test to ensure isolation.

---

### `tests/test_transaction_hyp_routes.py`

**Purpose:**  
Uses Hypothesis for property-based testing of the API, ensuring robustness against a wide range of inputs.

**Tests:**

- **`test_post_transaction_hypothesis`**  
  - Generates many valid combinations of `nome`, `mcc`, and `valor`.
  - Posts each to `/transacoes/`.
  - Asserts response is 201 (created) or 409 (duplicate).
  - If created, checks that returned data matches input.

- **`test_get_transactions_returns_list`**  
  - Calls `/transacoes/`.
  - Asserts the response is a list (even if empty).

- **`test_post_transaction_invalid_data`**  
  - Generates invalid payloads (empty `nome`, short `mcc`, zero or negative `valor`).
  - Posts each to `/transacoes/`.
  - Asserts the API returns a 422 Unprocessable Entity error.

---

### `tests/test_transaction_routes.py`

**Purpose:**  
Standard endpoint tests using realistic data.

**Tests:**

- **`test_post_transaction`**  
  - Posts a valid transaction.
  - Checks for 201 response and correct data.

- **`test_get_transactions`**  
  - Gets all transactions.
  - Checks for a 200 response and a list.

- **`test_get_transactions_by_mcc`**  
  - Gets transactions filtered by MCC.
  - Checks for a 200 response and a list.

- **`test_post_transaction_with_mcc`**  
  - Mocks the external MCC API call.
  - Posts a transaction to `/transacoes/with-mcc`.
  - Checks for 201 response.

---

### `tests/test_transaction_schema.py`

**Purpose:**  
Tests Pydantic schema validation.

**Tests:**

- **`test_valid_transaction_schema`**  
  - Asserts that a valid payload creates a `TransactionCreate` object.

- **`test_invalid_transaction_schema`**  
  - Asserts that invalid data (e.g., `mcc` is `None`, `valor` is a string) raises a `ValidationError`.

---

### `tests/unit/test_transaction_crud.py`

**Purpose:**  
Unit tests for database CRUD operations.

**Tests:**

- **`test_create_and_get_transaction`**  
  - Creates a transaction and retrieves it by name and value.

- **`test_get_db_transactions`**  
  - Inserts multiple transactions and tests pagination.

- **`test_get_db_transactions_by_mcc`**  
  - Inserts transactions with different MCCs and tests filtering.

---

### `tests/unit/test_processor.py`

**Purpose:**  
Unit and property-based tests for ETL processor logic, including async MCC API calls.

**Tests:**

- **`test_process_and_load_transaction_creates_new_transaction`**  
  - Uses Hypothesis to test that new transactions are created if not duplicates.

- **`test_process_and_load_transaction_raises_conflict`**  
  - Tests that a duplicate transaction raises a 409 error.

- **`test_call_mcc_api_success`**  
  - Mocks a successful MCC API call.

- **`test_call_mcc_api_http_error`**  
  - Mocks an HTTP error from the MCC API.

- **`test_call_mcc_api_request_error`**  
  - Mocks a network error from the MCC API.

- **`test_call_mcc_api_unexpected_error`**  
  - Mocks an unexpected error from the MCC API.

- **`test_process_and_create_transaction_with_mcc_request_success`**  
  - Tests the full ETL flow with a successful MCC API call.

- **`test_process_and_create_transaction_with_mcc_request_mcc_error`**  
  - Tests the ETL flow when the MCC API returns an error.

---

## Running the Tests

1. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Run all tests:**
   ```
   pytest -v
   ```

3. **Run only property-based tests:**
   ```
   pytest tests/test_transaction_hyp_routes.py
   ```

---

### About the MCC API (`mcc-api/`)

### Purpose

The **MCC API** is a standalone FastAPI microservice that provides Merchant Category Code (MCC) data. It is used by the Transaction API to enrich transactions with MCC descriptions and to validate MCC codes.

### Structure

```
mcc-api/
│
├── main.py            # FastAPI app for MCC lookup
├── mcc.json           # MCC code and description data
├── test_main.py       # Tests for MCC API
├── requirements.txt   # Python dependencies
├── ReadMe.md          # Quick start for MCC API
└── Help.md            # Development notes
```

### Features

- **List All MCCs:**  
  `GET /mcc` returns all available MCC codes and their descriptions.

- **Lookup MCC by Code:**  
  `GET /mcc/{code}` returns the description for a specific MCC code, or a 404 if not found.

- **Data Source:**  
  Reads from `mcc.json`, a file containing a comprehensive list of MCC codes and descriptions.

- **Validation:**  
  Uses Pydantic models to ensure data integrity.

### Example Usage

- **Start the API:**  
  ```sh
  uvicorn main:app --reload --port 8001
  ```
- **Get all MCCs:**  
  ```
  GET http://localhost:8001/mcc
  ```
- **Get a specific MCC:**  
  ```
  GET http://localhost:8001/mcc/5812
  ```

### Tests

- **`test_main.py`**  
  - Tests listing all MCCs.
  - Tests looking up an MCC by code (found and not found).
  - Uses mocking to simulate different data scenarios.

---


## Notes

- The test database (`test.db`) is automatically created and reset for each test run.
- The application is designed for extensibility; you can add more endpoints, models, or tests as needed.
- Property-based tests with Hypothesis help uncover edge cases by generating a wide range of input data.

---

## License

MIT License