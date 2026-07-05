# Bank Transaction History System

A Flask-based API (with a lightweight web UI) for recording and reporting bank transactions. This system uses a **singly linked list with a tail pointer** to store transactions and provides **pre-calculated monthly statistics** for fast reporting.

## Features

- Add transactions (deposits/withdrawals) via REST API or the web UI
- O(1) append via a tail pointer on the transaction linked list
- Automatic monthly and yearly aggregation of statistics
- Merge-sort algorithm for sorting transactions by ID
- Retrieve reports for a specific month or the entire year
- Reject duplicate transaction IDs and invalid transaction payloads at the API boundary

## Requirements

- Python 3.x
- Flask
- Requests (used by `test_api.py`)

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Server

Start the Flask API server:

```bash
python server.py
```

The server runs on `http://127.0.0.1:5000` by default. Open that URL in a browser for the web UI (add a transaction and view monthly/yearly reports), or call the JSON API directly as described below.

## API Endpoints

### 1. Add a Transaction

**POST** `/transaction`

Add a new transaction to the log.

**Request Body (JSON):**

| Field | Type | Description |
|---|---|---|
| `transaction_id` | string | Unique transaction identifier |
| `transaction_type` | string | Either `"deposit"` or `"withdrawal"` |
| `amount` | number | Transaction amount |
| `timestamp` | string | ISO 8601 timestamp (e.g., `"2025-01-15T10:30:00"`) |
| `balance_after` | number | Account balance after the transaction |

**Example request:**

```bash
curl -X POST http://127.0.0.1:5000/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "T001",
    "transaction_type": "deposit",
    "amount": 5000.00,
    "timestamp": "2025-01-15T10:30:00",
    "balance_after": 15000.00
  }'
```

**Response (201 Created):**

```json
{
  "message": "Transaction added successfully"
}
```

**Response (400 Bad Request)** - if required fields are missing:

```json
{
  "error": "Missing required fields: transaction_type, amount, timestamp, balance_after"
}
```

Other validation rules enforced by `POST /transaction`:

- `transaction_id` must be a non-empty string after trimming whitespace
- `transaction_type` must be exactly `"deposit"` or `"withdrawal"`
- `amount` must be numeric, must not be a boolean, and must be greater than `0`
- `balance_after` must be numeric and must not be a boolean; negative balances are allowed
- `timestamp` must be a valid ISO 8601 datetime string
- Duplicate `transaction_id` values are rejected with **409 Conflict**

### 2. Get a Monthly or Yearly Report

**GET** `/report/<month>`

Retrieve aggregated statistics for a specific month or the full year.

**Path Parameters:**

| Parameter | Description |
|---|---|
| `month` | An integer `1`-`12` for a specific month, or `"all"` for the yearly report |

**Examples:**

Get the report for January (month 1):

```bash
curl http://127.0.0.1:5000/report/1
```

**Response:**

```json
{
  "month": 1,
  "total_income": 5000.0,
  "total_expense": 2000.0,
  "txn_count": 2,
  "ending_balance": 13000.0
}
```

Get the full yearly report:

```bash
curl http://127.0.0.1:5000/report/all
```

**Response:**

```json
{
  "month_1": {
    "total_income": 5000.0,
    "total_expense": 2000.0,
    "txn_count": 2,
    "ending_balance": 13000.0
  },
  "month_2": {
    "total_income": 3000.0,
    "total_expense": 1500.0,
    "txn_count": 2,
    "ending_balance": 14500.0
  },
  "...": "...",
  "yearly_total": {
    "total_income": 15000.0,
    "total_expense": 3500.0,
    "txn_count": 5,
    "ending_balance": 21500.0
  }
}
```

## Running Tests

A test suite is included. Start the server first, then run:

```bash
python test_api.py
```

The script prompts before running and then performs assertion-based checks against the live server.

## Project Structure

| File | Description |
|---|---|
| `server.py` | Flask API with POST/GET endpoints + `/` UI route |
| `database.py` | System's data structure |
| `app.py` | Core logic: linked list (tail pointer), sorting, statistics |
| `templates/index.html` | Web UI: add-transaction form + report viewer |
| `static/style.css` | Web UI styling |
| `static/app.js` | Web UI logic (fetch calls to the API) |
| `test_api.py` | Assertion-based test script for the API endpoints |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |
