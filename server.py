from flask import Flask, request, jsonify
from app import TransactionLog, PrecalculatedStats, TransactionNode


app = Flask(__name__)
transaction_log = TransactionLog()

# Load existing transactions from JSON on startup
transaction_log.load_from_storage()

# POST /transaction
@app.route("/transaction", methods=["POST"])
def add_transaction():
    data = request.get_json()
    transaction_id = data.get("transaction_id")
    transaction_type = data.get("transaction_type")
    amount = data.get("amount")
    timestamp = data.get("timestamp")
    balance_after = data.get("balance_after")

    # Validate input
    if not all([transaction_id, transaction_type, amount, timestamp, balance_after]):
        return jsonify({"error": "Missing required fields"}), 400

    # Insert the transaction into the log
    transaction_log.insert_transaction(transaction_id, transaction_type, amount, timestamp, balance_after)
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