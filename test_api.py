"""
Test script for the Flask bank transaction API.
Tests: POST /transaction and GET /report/<month> endpoints
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

def print_separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_add_transaction(txn_id, txn_type, amount, timestamp, balance_after):
    url = f"{BASE_URL}/transaction"
    payload = {
        "transaction_id": txn_id,
        "transaction_type": txn_type,
        "amount": amount,
        "timestamp": timestamp,
        "balance_after": balance_after
    }
    print(f"\n--> POST /transaction")
    print(f"    Payload: {json.dumps(payload)}")
    try:
        resp = requests.post(url, json=payload, timeout=5)
        print(f"    Status: {resp.status_code}")
        print(f"    Response: {resp.json()}")
        return resp
    except requests.exceptions.ConnectionError:
        print("    ERROR: Connection refused. Is the server running?")
        return None
    except Exception as e:
        print(f"    ERROR: {e}")
        return None

def test_get_report(month):
    url = f"{BASE_URL}/report/{month}"
    print(f"\n--> GET /report/{month}")
    try:
        resp = requests.get(url, timeout=5)
        print(f"    Status: {resp.status_code}")
        print(f"    Response: {json.dumps(resp.json(), indent=4)}")
        return resp
    except requests.exceptions.ConnectionError:
        print("    ERROR: Connection refused. Is the server running?")
        return None
    except Exception as e:
        print(f"    ERROR: {e}")
        return None

def test_invalid_payload():
    url = f"{BASE_URL}/transaction"
    payload = {"transaction_id": "T001"}
    print(f"\n--> POST /transaction (missing fields)")
    print(f"    Payload: {json.dumps(payload)}")
    try:
        resp = requests.post(url, json=payload, timeout=5)
        print(f"    Status: {resp.status_code}")
        print(f"    Response: {resp.json()}")
    except requests.exceptions.ConnectionError:
        print("    ERROR: Connection refused. Is the server running?")
    except Exception as e:
        print(f"    ERROR: {e}")

def test_invalid_month():
    for month in [0, 13, "abc"]:
        test_get_report(month)

def main():
    print("="*60)
    print("  BANK TRANSACTION API TEST SUITE")
    print("="*60)
    print(f"\nMake sure the Flask server is running at {BASE_URL}")
    print(f"Run the server in another terminal using the venv python")

    input("\nPress Enter to continue if server is running, or Ctrl+C to quit: ")

    print_separator("TEST 1: Add valid transactions")
    test_add_transaction("T001", "deposit", 5000.00, "2025-01-15T10:30:00", 15000.00)
    test_add_transaction("T002", "withdrawal", 2000.00, "2025-01-20T14:00:00", 13000.00)
    test_add_transaction("T003", "deposit", 3000.00, "2025-02-10T09:15:00", 16000.00)
    test_add_transaction("T004", "withdrawal", 1500.00, "2025-02-25T16:45:00", 14500.00)
    test_add_transaction("T005", "deposit", 7000.00, "2025-03-05T11:00:00", 21500.00)

    print_separator("TEST 2: Missing fields (expect 400)")
    test_invalid_payload()

    print_separator("TEST 3: Report for January (month=1)")
    test_get_report(1)

    print_separator("TEST 4: Report for February (month=2)")
    test_get_report(2)

    print_separator("TEST 5: Report for March (month=3)")
    test_get_report(3)

    print_separator("TEST 6: Report for all months (GET /report/all)")
    test_get_report("all")

    print_separator("TEST 7: Invalid month values")
    test_invalid_month()

    print("\n" + "="*60)
    print("  ALL TESTS COMPLETED")
    print("="*60)

if __name__ == "__main__":
    main()
