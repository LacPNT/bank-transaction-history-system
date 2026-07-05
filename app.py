from datetime import datetime

from database import TransactionNode, MonthStats, save_to_json, load_from_json


class MergeSort:
    """Merge sort algorithm for sorting a TransactionNode linked list by transaction_id."""

    @staticmethod
    def _split_list(head):
        """Split the linked list into two halves using slow/fast pointer."""
        if not head or not head.next:
            return head, None

        slow = head
        fast = head.next

        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next

        mid = slow.next
        slow.next = None  # Split into two lists
        return head, mid

    @staticmethod
    def _sorted_merge(left, right):
        """Merge two sorted linked lists by transaction_id (ascending)."""
        if not left:
            return right
        if not right:
            return left

        if left.transaction_id <= right.transaction_id:
            result = left
            result.next = MergeSort._sorted_merge(left.next, right)
        else:
            result = right
            result.next = MergeSort._sorted_merge(left, right.next)

        return result

    @staticmethod
    def sort(head):
        """Sort the linked list starting at `head` by transaction_id (ascending).
        Returns the new head of the sorted list."""
        if not head or not head.next:
            return head

        left, right = MergeSort._split_list(head)
        left = MergeSort.sort(left)
        right = MergeSort.sort(right)

        return MergeSort._sorted_merge(left, right)


class TransactionLog:
    def __init__(self):
        self.head = None
        self.tail = None
        self.stats = PrecalculatedStats()

    def sort_by_id(self):
        """Sort transactions by transaction_id using merge sort (ascending)."""
        self.head = MergeSort.sort(self.head)
        # Merge sort changes which node is last, so the tail pointer must be
        # recomputed to keep future appends O(1).
        current = self.head
        while current and current.next:
            current = current.next
        self.tail = current

    def search_by_id(self, transaction_id):
        """Linear search over the insertion-order linked list. O(n) worst case."""
        current = self.head
        while current:
            if current.transaction_id == transaction_id:
                return current
            current = current.next
        return None

    def insert_transaction(self, transaction_id, transaction_type, amount, timestamp, balance_after):
        # Parse timestamp string to datetime object
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp)
        else:
            dt = timestamp

        # Create new node and append at the tail - O(1) via the tail pointer,
        # instead of traversing the whole list on every insert.
        new_node = TransactionNode(transaction_id, transaction_type, amount, dt, balance_after)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node

        # Update stats
        month = dt.month
        self.stats.update_stats(transaction_type, amount, month, balance_after)

        # Persist to JSON file
        save_to_json(self.head)

    def load_from_storage(self):
        """Load transactions from JSON file into the linked list."""
        self.head = load_from_json()
        # Rebuild stats from loaded data and recompute the tail pointer
        self.stats = PrecalculatedStats()
        self.tail = None
        current = self.head
        while current:
            month = current.timestamp.month if current.timestamp else 0
            self.stats.update_stats(
                current.transaction_type, current.amount, month, current.balance_after
            )
            self.tail = current
            current = current.next

    def display_transactions(self):
        """Display all transactions in the log."""
        current = self.head
        while current:
            print(
                f"Transaction ID: {current.transaction_id}, Type: {current.transaction_type}, "
                f"Amount: {current.amount}, Timestamp: {current.timestamp}, "
                f"Balance After: {current.balance_after}"
            )
            current = current.next


class PrecalculatedStats:
    def __init__(self):
        self.months = [MonthStats() for _ in range(13)]

    def update_stats(self, transaction_type, amount, month=0, balance_after=None):
        target = self.months[month]
        if transaction_type == "deposit":
            target.total_income += amount
        elif transaction_type == "withdrawal":
            target.total_expense += amount
        target.txn_count += 1
        if balance_after is not None:
            target.ending_balance = balance_after

        if month != 0:
            yearly = self.months[0]
            if transaction_type == "deposit":
                yearly.total_income += amount
            elif transaction_type == "withdrawal":
                yearly.total_expense += amount
            yearly.txn_count += 1
            if balance_after is not None:
                yearly.ending_balance = balance_after

    def get_report(self, month=None):
        """Get report for a specific month (1-12) or all months (default)."""
        if month is not None:
            target = self.months[month]
            return {
                "month": month,
                "total_income": target.total_income,
                "total_expense": target.total_expense,
                "txn_count": target.txn_count,
                "ending_balance": target.ending_balance,
            }
        report = {}
        for i in range(1, 13):
            m = self.months[i]
            report[f"month_{i}"] = {
                "total_income": m.total_income,
                "total_expense": m.total_expense,
                "txn_count": m.txn_count,
                "ending_balance": m.ending_balance,
            }
        report["yearly_total"] = {
            "total_income": self.months[0].total_income,
            "total_expense": self.months[0].total_expense,
            "txn_count": self.months[0].txn_count,
            "ending_balance": self.months[0].ending_balance,
        }
        return report

    def display_monthly_stats(self):
        """Print a readable summary of all months."""
        print("\n--- Monthly Statistics ---")
        for i in range(1, 13):
            m = self.months[i]
            print(
                f"Month {i:2d}: Income={m.total_income:>8.2f}, Expense={m.total_expense:>8.2f}, "
                f"Txns={m.txn_count:>4d}, Balance={m.ending_balance:>8.2f}"
            )
        y = self.months[0]
        print(
            f"Year : Income={y.total_income:>8.2f}, Expense={y.total_expense:>8.2f}, "
            f"Txns={y.txn_count:>4d}, Balance={y.ending_balance:>8.2f}"
        )
