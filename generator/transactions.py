import random
from datetime import datetime, timedelta
import uuid

from utils.helpers import generate_uuid, generate_timestamp, to_datetime, split_transaction

# Common payment types
PAYMENT_TYPES = ["wire", "credit_card", "ach", "check", "cash"]

def generate_legit_transactions(accounts, n=1000, start_date="2025-01-01", end_date="2025-01-31"):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    transactions = []

    individual_accounts = [acct for acct in accounts if acct.owner_type == "Person"]

    for _ in range(n):
        payment_type = random.choice(PAYMENT_TYPES)
        timestamp = generate_timestamp(start_dt, end_dt).strftime("%Y-%m-%d %H:%M:%S")
        amount = round(random.uniform(50, 5000), 2)
        txn_id = generate_uuid()

        if payment_type == "cash":
            if not individual_accounts:
                continue  # no eligible targets
            src = None
            tgt = random.choice(individual_accounts)
            source_description = "cash_deposit"
        else:
            src, tgt = random.sample(accounts, 2)
            while src.id == tgt.id:
                src, tgt = random.sample(accounts, 2)
            source_description = ""

        # Generate ledger-style entries
        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=src,
            tgt=tgt,
            amount=amount,
            currency=random.choice([tgt.currency]),
            payment_type=payment_type,
            is_laundering=False,
            source_description=source_description
        )

        transactions.extend(entries)

    return transactions
