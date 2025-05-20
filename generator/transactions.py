import random
from datetime import datetime, timedelta
import uuid

# Payment types commonly used in financial transactions
PAYMENT_TYPES = ["wire", "credit_card", "ach", "check", "cash"]

def generate_timestamp(start_date, end_date):
    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start_date + timedelta(seconds=random_seconds)

def generate_legit_transactions(accounts, n=1000, start_date="2025-01-01", end_date="2025-01-31"):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    transactions = []
    for _ in range(n):
        src, tgt = random.sample(accounts, 2)
        if src.id == tgt.id:
            continue  # skip self-transactions

        txn = {
            "transaction_id": str(uuid.uuid4())[:12],
            "timestamp": generate_timestamp(start_dt, end_dt).strftime("%Y-%m-%d %H:%M:%S"),
            "source_account": src.id,
            "target_account": tgt.id,
            "amount": round(random.uniform(50, 5000), 2),
            "currency": random.choice([src.currency, tgt.currency]),
            "payment_type": random.choice(PAYMENT_TYPES),
            "is_laundering": False
        }
        transactions.append(txn)

    return transactions
