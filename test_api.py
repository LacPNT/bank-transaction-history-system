"""
Interactive test script for the Flask bank transaction API.
Runs assertion-based checks against the live server.
Database is reset ONCE at the start via POST /reset.
"""
import json
import uuid

import requests

BASE_URL = "http://127.0.0.1:5000"


def print_separator(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def post_transaction(payload, expected_status, expected_error_substring=None):
    url = f"{BASE_URL}/transaction"
    print(f"\n--> POST /transaction")
    print(f"    Payload: {json.dumps(payload)}")

    try:
        resp = requests.post(url, json=payload, timeout=5)
    except requests.exceptions.ConnectionError as exc:
        raise AssertionError("Connection refused. Is the server running?") from exc

    print(f"    Status: {resp.status_code}")
    print(f"    Response: {resp.json()}")
    assert resp.status_code == expected_status, (
        f"expected {expected_status}, got {resp.status_code}"
    )
    if expected_error_substring is not None:
        assert expected_error_substring in resp.json().get("error", ""), (
            f"expected error containing {expected_error_substring!r}, got {resp.json()}"
        )
    return resp


def test_add_transaction(txn_id, txn_type, amount, timestamp, balance_after=None,
                         expected_status=201, expected_error_substring=None):
    payload = {
        "transaction_id": txn_id,
        "transaction_type": txn_type,
        "amount": amount,
        "timestamp": timestamp,
    }
    if balance_after is not None:
        payload["balance_after"] = balance_after
    return post_transaction(payload, expected_status, expected_error_substring)


def test_get_report(month, expected_status, expected_error_substring=None):
    url = f"{BASE_URL}/report/{month}"
    print(f"\n--> GET /report/{month}")

    try:
        resp = requests.get(url, timeout=5)
    except requests.exceptions.ConnectionError as exc:
        raise AssertionError("Connection refused. Is the server running?") from exc

    print(f"    Status: {resp.status_code}")
    print(f"    Response: {json.dumps(resp.json(), indent=4)}")
    assert resp.status_code == expected_status, (
        f"expected {expected_status}, got {resp.status_code}"
    )
    if expected_error_substring is not None:
        assert expected_error_substring in resp.json().get("error", ""), (
            f"expected error containing {expected_error_substring!r}, got {resp.json()}"
        )
    return resp


def test_invalid_payload():
    payload = {"transaction_id": "T001"}
    return post_transaction(payload, 400, "Missing required fields")


def test_invalid_month():
    test_get_report(13, 400, "Month must be between 1 and 12")


def main():
    print("=" * 60)
    print("  BANK TRANSACTION API TEST SUITE")
    print("=" * 60)
    print(f"\nMake sure the Flask server is running at {BASE_URL}")
    print("Run the server in another terminal using the venv python")

    input("\nPress Enter to continue if server is running, or Ctrl+C to quit: ")

    # Reset database ONCE so every run starts clean
    resp = requests.post(f"{BASE_URL}/reset", timeout=5)
    assert resp.status_code == 200, f"Reset failed: {resp.json()}"
    print("\n    [Database reset]\n")

    run_id = uuid.uuid4().hex[:8]

    # Balance chain (each test adds to the previous):
    # T01: Jan +5000 → 5000
    # T02: Jan -2000 → 3000
    # T03: Feb +3000 → 6000
    # T09: Mar +7000 → 13000

    print_separator("TEST 1: Add valid transactions (balance_after auto-calculated)")
    test_add_transaction(f"T{run_id}01", "deposit", 5000.00, "2025-01-15T10:30:00")
    test_add_transaction(f"T{run_id}02", "withdrawal", 2000.00, "2025-01-20T14:00:00")

    # Jan: income=5000, expense=2000, balance=3000
    resp = test_get_report(1, 200)
    data = resp.json()
    assert data["total_income"] == 5000.0
    assert data["total_expense"] == 2000.0
    assert data["ending_balance"] == 3000.0

    print_separator("TEST 2: balance_after auto-calculation (cumulative chain)")
    test_add_transaction(f"T{run_id}03", "deposit", 3000.00, "2025-02-10T09:15:00")

    # Jan: still 5000/2000/3000. Feb: income=3000, balance=6000
    resp = test_get_report(2, 200)
    data = resp.json()
    assert data["total_income"] == 3000.0
    assert data["ending_balance"] == 6000.0

    print_separator("TEST 3: Missing fields (expect 400)")
    test_invalid_payload()

    print_separator("TEST 4: Invalid amount checks")
    test_add_transaction(
        f"T{run_id}05",
        "deposit",
        0,
        "2025-03-05T11:00:00",
        expected_status=400,
        expected_error_substring="amount must be a numeric value greater than 0",
    )
    test_add_transaction(
        f"T{run_id}06",
        "deposit",
        True,
        "2025-03-06T11:00:00",
        expected_status=400,
        expected_error_substring="amount must be a numeric value greater than 0",
    )
    test_add_transaction(
        f"T{run_id}06B",
        "deposit",
        100.00,
        "2025-03-06T11:05:00",
        balance_after=False,
        expected_status=400,
        expected_error_substring="balance_after must be a numeric value",
    )

    print_separator("TEST 5: Invalid transaction type")
    test_add_transaction(
        f"T{run_id}07",
        "transfer",
        100.00,
        "2025-03-07T11:00:00",
        expected_status=400,
        expected_error_substring="transaction_type must be 'deposit' or 'withdrawal'",
    )

    print_separator("TEST 6: Invalid timestamp")
    test_add_transaction(
        f"T{run_id}08",
        "deposit",
        100.00,
        "not-a-timestamp",
        expected_status=400,
        expected_error_substring="timestamp must be a valid ISO 8601 datetime string",
    )

    print_separator("TEST 7: Duplicate transaction ID")
    duplicate_id = f"T{run_id}09"
    test_add_transaction(duplicate_id, "deposit", 7000.00, "2025-03-05T11:00:00")
    test_add_transaction(
        duplicate_id,
        "deposit",
        7100.00,
        "2025-03-06T11:00:00",
        expected_status=409,
        expected_error_substring="transaction_id already exists",
    )

    print_separator("TEST 8: Report for all months (GET /report/all)")
    resp = test_get_report("all", 200)
    data = resp.json()
    # Cumulative: Jan(5000i,2000e,3000bal) + Feb(3000i,6000bal) + Mar(7000i,13000bal)
    assert data["month_1"]["total_income"] == 5000.0
    assert data["month_1"]["total_expense"] == 2000.0
    assert data["month_1"]["ending_balance"] == 3000.0
    assert data["month_2"]["total_income"] == 3000.0
    assert data["month_2"]["ending_balance"] == 6000.0
    assert data["month_3"]["total_income"] == 7000.0
    assert data["month_3"]["ending_balance"] == 13000.0
    assert data["yearly_total"]["total_income"] == 15000.0
    assert data["yearly_total"]["total_expense"] == 2000.0
    assert data["yearly_total"]["ending_balance"] == 13000.0

    print_separator("TEST 9: Invalid month values")
    test_invalid_month()

    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
