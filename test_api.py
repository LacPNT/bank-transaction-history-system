"""
Interactive test script for the Flask bank transaction API.
Runs assertion-based checks against the live server.
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


def test_add_transaction(txn_id, txn_type, amount, timestamp, balance_after,
                         expected_status=201, expected_error_substring=None):
    payload = {
        "transaction_id": txn_id,
        "transaction_type": txn_type,
        "amount": amount,
        "timestamp": timestamp,
        "balance_after": balance_after,
    }
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

    run_id = uuid.uuid4().hex[:8]

    print_separator("TEST 1: Add valid transactions")
    test_add_transaction(f"T{run_id}01", "deposit", 5000.00, "2025-01-15T10:30:00", 15000.00)
    test_add_transaction(f"T{run_id}02", "withdrawal", 2000.00, "2025-01-20T14:00:00", 13000.00)

    print_separator("TEST 2: balance_after edge cases")
    test_add_transaction(f"T{run_id}03", "deposit", 3000.00, "2025-02-10T09:15:00", 0)
    test_add_transaction(f"T{run_id}04", "withdrawal", 1500.00, "2025-02-25T16:45:00", -500.00)

    print_separator("TEST 3: Missing fields (expect 400)")
    test_invalid_payload()

    print_separator("TEST 4: Invalid amount checks")
    test_add_transaction(
        f"T{run_id}05",
        "deposit",
        0,
        "2025-03-05T11:00:00",
        21500.00,
        400,
        "amount must be a numeric value greater than 0",
    )
    test_add_transaction(
        f"T{run_id}06",
        "deposit",
        True,
        "2025-03-06T11:00:00",
        21500.00,
        400,
        "amount must be a numeric value greater than 0",
    )
    test_add_transaction(
        f"T{run_id}06B",
        "deposit",
        100.00,
        "2025-03-06T11:05:00",
        False,
        400,
        "balance_after must be a numeric value",
    )

    print_separator("TEST 5: Invalid transaction type")
    test_add_transaction(
        f"T{run_id}07",
        "transfer",
        100.00,
        "2025-03-07T11:00:00",
        21600.00,
        400,
        "transaction_type must be 'deposit' or 'withdrawal'",
    )

    print_separator("TEST 6: Invalid timestamp")
    test_add_transaction(
        f"T{run_id}08",
        "deposit",
        100.00,
        "not-a-timestamp",
        21600.00,
        400,
        "timestamp must be a valid ISO 8601 datetime string",
    )

    print_separator("TEST 7: Duplicate transaction ID")
    duplicate_id = f"T{run_id}09"
    test_add_transaction(duplicate_id, "deposit", 7000.00, "2025-03-05T11:00:00", 21500.00)
    test_add_transaction(
        duplicate_id,
        "deposit",
        7100.00,
        "2025-03-06T11:00:00",
        28600.00,
        409,
        "transaction_id already exists",
    )

    print_separator("TEST 8: Report for all months (GET /report/all)")
    test_get_report("all", 200)

    print_separator("TEST 9: Invalid month values")
    test_invalid_month()

    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
