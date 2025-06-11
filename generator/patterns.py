import random
import uuid
from datetime import datetime
from generator.transactions import PAYMENT_TYPES, ATM_LIMIT
from utils.helpers import (
    to_datetime,
    generate_uuid,
    split_transaction,
    describe_transaction,
    generate_transaction_timestamp,
    generate_post_date,
    safe_sample,
)

def inject_patterns(accounts, pattern_config, known_accounts=None):
    laundering_transactions = []

    for pattern in pattern_config.get("patterns", []):
        pattern_type = pattern["type"]
        for _ in range(pattern["instances"]):
            if pattern_type == "cycle":
                txns = inject_cycle_pattern(accounts, pattern, known_accounts)
            elif pattern_type == "fan_out":
                txns = inject_fan_out_pattern(accounts, pattern, known_accounts)
            elif pattern_type == "scatter_gather":
                txns = inject_scatter_gather_pattern(accounts, pattern, known_accounts)
            elif pattern_type == "fan_in":
                txns = inject_fan_in_pattern(accounts, pattern, known_accounts)
            elif pattern_type == "cash_structuring":
                txns = inject_cash_structuring_pattern(accounts, pattern, known_accounts)
            else:
                print(f"Unsupported pattern type: {pattern_type}")
                continue

            laundering_transactions.extend(txns)

    return laundering_transactions


def inject_cycle_pattern(accounts, pattern, known_accounts):
    count = pattern.get("accounts_per_cycle", 3)
    amount = pattern.get("amount", 1000)
    currency = pattern.get("currency", "USD")
    start_dt = to_datetime(pattern["start_date"])
    end_dt = to_datetime(pattern["end_date"])

    selected = safe_sample(accounts, count)
    actual_count = len(selected)
    if actual_count < 2:
        return []

    transactions = []
    safe_payment_types = [p for p in PAYMENT_TYPES if p != "cash"]

    for i in range(actual_count):
        src = selected[i]
        tgt = selected[(i + 1) % actual_count]
        txn_id = generate_uuid()
        ts_dt = generate_transaction_timestamp(start_dt, end_dt, override_hours=True)
        timestamp = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
        post_date = generate_post_date(ts_dt).strftime("%Y-%m-%d %H:%M:%S")

        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=src,
            tgt=tgt,
            amount=round(amount, 2),
            currency=currency,
            payment_type=random.choice(safe_payment_types),
            is_laundering=True,
            known_accounts=known_accounts,
            post_date=post_date
        )
        transactions.extend(entries)

    return transactions


def inject_fan_out_pattern(accounts, pattern, known_accounts):
    num_targets = pattern.get("targets_per_source", 3)
    amount = pattern.get("amount_per_target", 500)
    currency = pattern.get("currency", "USD")
    start_dt = to_datetime(pattern["start_date"])
    end_dt = to_datetime(pattern["end_date"])

    safe_payment_types = [p for p in PAYMENT_TYPES if p != "cash"]

    source = random.choice(accounts)
    targets = safe_sample([a for a in accounts if a.id != source.id], num_targets)

    transactions = []
    for tgt in targets:
        txn_id = generate_uuid()
        ts_dt = generate_transaction_timestamp(start_dt, end_dt, override_hours=True)
        timestamp = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
        post_date = generate_post_date(ts_dt).strftime("%Y-%m-%d %H:%M:%S")

        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=source,
            tgt=tgt,
            amount=round(amount, 2),
            currency=currency,
            payment_type=random.choice(safe_payment_types),
            is_laundering=True,
            known_accounts=known_accounts,
            post_date=post_date
        )
        transactions.extend(entries)

    return transactions


def inject_scatter_gather_pattern(accounts, pattern, known_accounts):
    sources = pattern.get("sources", 1)
    intermediates = pattern.get("intermediates", 3)
    sinks = pattern.get("sinks", 1)
    total_amount = pattern.get("total_amount", 5000)
    currency = pattern.get("currency", "USD")
    start_dt = to_datetime(pattern["start_date"])
    end_dt = to_datetime(pattern["end_date"])

    safe_payment_types = [p for p in PAYMENT_TYPES if p != "cash"]

    accounts_pool = list(accounts)
    random.shuffle(accounts_pool)

    src_accounts = [accounts_pool.pop() for _ in range(min(sources, len(accounts_pool)))]
    int_accounts = [accounts_pool.pop() for _ in range(min(intermediates, len(accounts_pool)))]
    sink_accounts = [accounts_pool.pop() for _ in range(min(sinks, len(accounts_pool)))]

    if not src_accounts or not int_accounts or not sink_accounts:
        return []

    transactions = []

    # Scatter: sources → intermediates
    for src in src_accounts:
        for int_acct in int_accounts:
            txn_id = generate_uuid()
            ts_dt = generate_transaction_timestamp(start_dt, end_dt, override_hours=True)
            timestamp = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
            post_date = generate_post_date(ts_dt).strftime("%Y-%m-%d %H:%M:%S")

            entries = split_transaction(
                txn_id=txn_id,
                timestamp=timestamp,
                src=src,
                tgt=int_acct,
                amount=round(total_amount / max(1, len(src_accounts) * len(int_accounts)), 2),
                currency=currency,
                payment_type=random.choice(safe_payment_types),
                is_laundering=True,
                known_accounts=known_accounts,
                post_date=post_date
            )
            transactions.extend(entries)

    # Gather: intermediates → sinks
    for int_acct in int_accounts:
        for sink in sink_accounts:
            txn_id = generate_uuid()
            ts_dt = generate_transaction_timestamp(start_dt, end_dt, override_hours=True)
            timestamp = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
            post_date = generate_post_date(ts_dt).strftime("%Y-%m-%d %H:%M:%S")

            entries = split_transaction(
                txn_id=txn_id,
                timestamp=timestamp,
                src=int_acct,
                tgt=sink,
                amount=round(total_amount / max(1, len(int_accounts) * len(sink_accounts)), 2),
                currency=currency,
                payment_type=random.choice(safe_payment_types),
                is_laundering=True,
                known_accounts=known_accounts,
                post_date=post_date
            )
            transactions.extend(entries)

    return transactions

def inject_fan_in_pattern(accounts, pattern, known_accounts):
    sources_per_target = pattern.get("sources_per_target", 5)
    amount_per_source = pattern.get("amount_per_source", 200)
    currency = pattern.get("currency", "USD")
    start_dt = to_datetime(pattern["start_date"])
    end_dt = to_datetime(pattern["end_date"])

    safe_payment_types = [p for p in PAYMENT_TYPES if p != "cash"]

    transactions = []

    # Select one target and multiple unique sources
    target = random.choice(accounts)
    sources = safe_sample([a for a in accounts if a.id != target.id], sources_per_target)

    for src in sources:
        txn_id = generate_uuid()
        ts_dt = generate_transaction_timestamp(start_dt, end_dt, override_hours=True)
        timestamp = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
        post_date = generate_post_date(ts_dt).strftime("%Y-%m-%d %H:%M:%S")
        payment_type = random.choice(safe_payment_types)

        sd = (
            describe_transaction(payment_type, "Fan-in Structuring")
            if payment_type.lower() != "ach"
            else ""
        )

        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=src,
            tgt=target,
            amount=round(amount_per_source, 2),
            currency=currency,
            payment_type=payment_type,
            is_laundering=True,
            source_description=sd,
            known_accounts=known_accounts,
            post_date=post_date
        )

        transactions.extend(entries)

    return transactions


def inject_cash_structuring_pattern(accounts, pattern, known_accounts):
    accounts_per_pattern = pattern.get("accounts", 1)
    txns_per_account = pattern.get("transactions_per_account", 5)
    max_deposit = pattern.get("max_deposit", 10000)
    atm_ratio = pattern.get("atm_ratio", 0.5)
    currency = pattern.get("currency", "USD")
    start_dt = to_datetime(pattern["start_date"])
    end_dt = to_datetime(pattern["end_date"])

    selected = safe_sample(accounts, accounts_per_pattern)

    transactions = []
    for acct in selected:
        for _ in range(txns_per_account):
            deposit = random.choice([True, False])
            channel = "ATM" if random.random() < atm_ratio else "Teller"
            if channel == "ATM":
                amount = random.uniform(100, ATM_LIMIT)
            else:
                amount = random.uniform(ATM_LIMIT, max_deposit)

            ts_dt = generate_transaction_timestamp(start_dt, end_dt, override_hours=True)
            timestamp = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
            post_date = generate_post_date(ts_dt).strftime("%Y-%m-%d %H:%M:%S")
            txn_id = generate_uuid()

            src = None if deposit else acct
            tgt = acct if deposit else None

            entries = split_transaction(
                txn_id=txn_id,
                timestamp=timestamp,
                src=src,
                tgt=tgt,
                amount=round(amount, 2),
                currency=currency,
                payment_type="cash",
                is_laundering=True,
                known_accounts=known_accounts,
                post_date=post_date,
                channel=channel,
            )
            transactions.extend(entries)

    return transactions
