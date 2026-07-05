from datetime import datetime

from flask import Flask, jsonify, render_template, request

from app import TransactionLog


app = Flask(__name__)
transaction_log = TransactionLog()

# Load existing transactions from JSON on startup
transaction_log.load_from_storage()


# GET / - serves the frontend (form to add a transaction + report viewer)
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


def _is_number(value):
    """Return True for int/float values, but reject booleans explicitly."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# POST /transaction
@app.route("/transaction", methods=["POST"])
def add_transaction():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "transaction_id",
        "transaction_type",
        "amount",
        "timestamp",
        "balance_after",
    ]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    transaction_id = data.get("transaction_id")
    transaction_type = data.get("transaction_type")
    amount = data.get("amount")
    timestamp = data.get("timestamp")
    balance_after = data.get("balance_after")

    if not isinstance(transaction_id, str) or not transaction_id.strip():
        return jsonify({"error": "transaction_id must be a non-empty string"}), 400
    transaction_id = transaction_id.strip()

    if transaction_type not in {"deposit", "withdrawal"}:
        return jsonify({"error": "transaction_type must be 'deposit' or 'withdrawal'"}), 400

    if not _is_number(amount) or amount <= 0:
        return jsonify({"error": "amount must be a numeric value greater than 0"}), 400

    if not _is_number(balance_after):
        return jsonify({"error": "balance_after must be a numeric value"}), 400

    if not isinstance(timestamp, str):
        return jsonify({"error": "timestamp must be an ISO 8601 string"}), 400

    try:
        datetime.fromisoformat(timestamp)
    except ValueError:
        return jsonify({"error": "timestamp must be a valid ISO 8601 datetime string"}), 400

    # Design decision: reject duplicate transaction_id (previously silently
    # accepted and double-counted in stats) - see Report 4 AI Audit Log / Human Delta.
    if transaction_log.search_by_id(transaction_id):
        return jsonify({"error": "transaction_id already exists"}), 409

    # Insert the transaction into the log
    transaction_log.insert_transaction(
        transaction_id, transaction_type, amount, timestamp, balance_after
    )
    return jsonify({"message": "Transaction added successfully"}), 201


# GET /report/<month>
@app.route("/report/<month>", methods=["GET"])
def get_report(month):
    stats = transaction_log.stats

    if month == "all":
        transactions = stats.get_report()
    else:
        try:
            month_int = int(month)
        except ValueError:
            return jsonify({"error": "Invalid month. Must be an integer (1-12) or 'all'."}), 400
        if month_int < 1 or month_int > 12:
            return jsonify({"error": "Month must be between 1 and 12."}), 400
        transactions = stats.get_report(month_int)
    return jsonify(transactions), 200


if __name__ == "__main__":
    app.run(debug=True)
