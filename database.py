import json
import os
from datetime import datetime


DATA_FILE = "transactions.json"


class TransactionNode:
    """Linked list node representing a bank transaction."""

    def __init__(self, transaction_id=None, transaction_type=None, amount=None,
                 timestamp=None, balance_after=None):
        self.transaction_id = transaction_id
        self.transaction_type = transaction_type
        self.amount = amount
        self.timestamp = timestamp
        self.balance_after = balance_after
        self.next = None

    def __repr__(self):
        return (f"<TransactionNode(id={self.transaction_id}, type={self.transaction_type}, "
                f"amount={self.amount}, timestamp={self.timestamp}, balance={self.balance_after})>")


class MonthStats:
    def __init__(self, total_income=0, total_expense=0, txn_count=0, ending_balance=0):
        self.total_income = total_income
        self.total_expense = total_expense
        self.txn_count = txn_count
        self.ending_balance = ending_balance


def save_to_json(head):
    """Save the linked list to a JSON file."""
    data = []
    current = head
    while current:
        data.append({
            "transaction_id": current.transaction_id,
            "transaction_type": current.transaction_type,
            "amount": current.amount,
            "timestamp": current.timestamp.isoformat() if isinstance(current.timestamp, datetime) else current.timestamp,
            "balance_after": current.balance_after
        })
        current = current.next

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def clear_storage():
    """Overwrite the JSON file with an empty array (reset database)."""
    with open(DATA_FILE, "w") as f:
        json.dump([], f)


def load_from_json():
    """Load the linked list from a JSON file. Returns the head node."""
    if not os.path.exists(DATA_FILE):
        return None

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if not data:
        return None

    head = None
    prev = None # Pointer
    for record in data:
        # Parse timestamp string back to datetime
        ts = record.get("timestamp")
        if ts and isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except ValueError:
                ts = None

        node = TransactionNode(
            transaction_id=record["transaction_id"],
            transaction_type=record["transaction_type"],
            amount=record["amount"],
            timestamp=ts,
            balance_after=record["balance_after"]
        )
        if head is None: # Using prev to keep the insertion order correct
            head = node
            prev = node
        else:
            prev.next = node
            prev = node

    return head
