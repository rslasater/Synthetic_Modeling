import random
import uuid
from datetime import datetime
from generator.transactions import generate_timestamp, PAYMENT_TYPES
from utils.helpers import to_datetime, generate_uuid, split_transaction


def inject_patterns(accounts, pattern_config):
    laundering_transactions = []

    for pattern in pattern_config.get("patterns", []):
        pattern_type = pattern["type"]
        for _ in range(pattern["instances"]):
            if pattern_type == "cycle":
                txns = inject_cycle_pattern(accounts, pattern)
            elif pattern_type == "fan_out":
                txns = inject_fan_out_pattern(accounts, pattern)
            elif pattern_type == "scatter_gather":
                txns = inject_scatter_gather_pattern(accounts, pattern)
            else:
                print(f"Unsupported pattern type: {pattern_type}")
                continue

            laundering_transactions.extend(txns)

    return laundering_transactions


def inject_cycle_pattern(accounts, pattern):
    count = pattern.get("accounts_per_cycle", 3)
    amount = pattern.get("amount", 1000)
    currency = pattern.get("currency", "USD")
    start_dt = to_datetime(pattern["start_date"])
    end_dt = to_datetime(pattern["end_date"])

    selected = random.sample(accounts, count)
    transactions = []
    safe_payment_types = [p for p in PAYMENT_TYPES if p != "cash"]

    for i in range(count):
        src = selected[i]
        tgt = selected[(i + 1) % count]
        txn_id = generate_uuid()
        timestamp = generate_timestamp(start_dt, end_dt).strftime("%Y-%m-%d %H:%M:%S")

        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=src,
            tgt=tgt,
            amount=round(amount, 2),
            currency=currency,
            payment_type=random.choice(safe_payment_types),
            is_laundering=True
        )
        transactions.extend(entries)

    return transactions


def inject_fan_out_pattern(accounts, pattern):
    num_targets = pattern.get("targets_per_source", 3)
    amount = pattern.get("amount_per_target", 500)
    currency = pattern.get("currency", "USD")
    start_dt = to_datetime(pattern["start_date"])
    end_dt = to_datetime(pattern["end_date"])

    safe_payment_types = [p for p in PAYMENT_TYPES if p != "cash"]

    source = random.choice(accounts)
    targets = random.sample([a for a in accounts if a.id != source.id], num_targets)

    transactions = []
    for tgt in targets:
        txn_id = generate_uuid()
        timestamp = generate_timestamp(start_dt, end_dt).strftime("%Y-%m-%d %H:%M:%S")

        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=source,
            tgt=tgt,
            amount=round(amount, 2),
            currency=currency,
            payment_type=random.choice(safe_payment_types),
            is_laundering=True
        )
        transactions.extend(entries)

    return transactions


def inject_scatter_gather_pattern(accounts, pattern):
    sources = pattern.get("sources", 1)
    intermediates = pattern.get("intermediates", 3)
    sinks = pattern.get("sinks", 1)
    total_amount = pattern.get("total_amount", 5000)
    currency = pattern.get("currency", "USD")
    start_dt = to_datetime(pattern["start_date"])
    end_dt = to_datetime(pattern["end_date"])

    safe_payment_types = [p for p in PAYMENT_TYPES if p != "cash"]

    selected = random.sample(accounts, sources + intermediates + sinks)
    src_accounts = selected[:sources]
    int_accounts = selected[sources:sources + intermediates]
    sink_accounts = selected[-sinks:]

    transactions = []

    # Scatter: sources → intermediates
    for src in src_accounts:
        for int_acct in int_accounts:
            txn_id = generate_uuid()
            timestamp = generate_timestamp(start_dt, end_dt).strftime("%Y-%m-%d %H:%M:%S")

            entries = split_transaction(
                txn_id=txn_id,
                timestamp=timestamp,
                src=src,
                tgt=int_acct,
                amount=round(total_amount / (sources * intermediates), 2),
                currency=currency,
                payment_type=random.choice(safe_payment_types),
                is_laundering=True
            )
            transactions.extend(entries)

    # Gather: intermediates → sinks
    for int_acct in int_accounts:
        for sink in sink_accounts:
            txn_id = generate_uuid()
            timestamp = generate_timestamp(start_dt, end_dt).strftime("%Y-%m-%d %H:%M:%S")

            entries = split_transaction(
                txn_id=txn_id,
                timestamp=timestamp,
                src=int_acct,
                tgt=sink,
                amount=round(total_amount / (intermediates * sinks), 2),
                currency=currency,
                payment_type=random.choice(safe_payment_types),
                is_laundering=True
            )
            transactions.extend(entries)

    return transactions
