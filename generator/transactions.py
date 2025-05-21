import random
from datetime import datetime
import uuid

from utils.helpers import generate_uuid, generate_timestamp, to_datetime, split_transaction, describe_transaction

# Common payment types
PAYMENT_TYPES = ["wire", "credit_card", "ach", "check", "cash"]

def generate_legit_transactions(accounts, entities, n=1000, start_date="2025-01-01", end_date="2025-01-31", known_accounts=None):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    known_accounts = set(known_accounts) if known_accounts else set()

    transactions = []
    attempts = 0
    skipped_visibility = 0
    skipped_known = 0
    skipped_payment_type = 0
    success = 0

    while success < n and attempts < n * 10:  # Avoid infinite loops
        attempts += 1

        src, tgt = random.sample(accounts, 2)
        while src.id == tgt.id:
            src, tgt = random.sample(accounts, 2)

        src_entity = next((e for e in entities if e.id == src.owner_id), None)
        tgt_entity = next((e for e in entities if e.id == tgt.owner_id), None)
        if not src_entity or not tgt_entity:
            continue

        if src_entity.visibility not in ["sender", "both"] or tgt_entity.visibility not in ["receiver", "both"]:
            skipped_visibility += 1
            continue

        if src.id not in known_accounts and tgt.id not in known_accounts:
            skipped_known += 1
            continue

        sender_rules = src_entity.get_allowed_transactions()
        if not sender_rules:
            skipped_payment_type += 1
            continue

        payment_type = random.choice(list(sender_rules.keys()))
        purpose = random.choice(sender_rules[payment_type])
        source_description = describe_transaction(payment_type, purpose)

        timestamp = generate_timestamp(start_dt, end_dt).strftime("%Y-%m-%d %H:%M:%S")
        amount = round(random.uniform(50, 5000), 2)
        txn_id = generate_uuid()

        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=src,
            tgt=tgt,
            amount=amount,
            currency="USD",
            payment_type=payment_type,
            is_laundering=False,
            source_description=source_description,
            known_accounts=known_accounts
        )

        transactions.extend(entries)
        success += 1

    print(f"[DEBUG] Attempted: {attempts}")
    print(f"[DEBUG] Success: {success}")
    print(f"[DEBUG] Skipped (visibility): {skipped_visibility}")
    print(f"[DEBUG] Skipped (unknown accounts): {skipped_known}")
    print(f"[DEBUG] Skipped (payment type issues): {skipped_payment_type}")

    return transactions
