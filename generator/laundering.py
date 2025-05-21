import random
from datetime import timedelta
from utils.helpers import generate_uuid, generate_timestamp, split_transaction, describe_transaction

def generate_laundering_chains(entities, accounts, known_accounts, start_date, end_date, n_chains=10):
    transactions = []
    launderers = [e for e in entities if getattr(e, "launderer", False)]

    for _ in range(n_chains):
        if len(launderers) == 0:
            break

        origin = random.choice(launderers)

        # Select a random layering pattern
        pattern_type = random.choice(["layering", "circular", "burst"])
        origin_acct = random.choice(origin.accounts)
        intermediaries = get_intermediaries(origin, entities, min_count=2)

        if not intermediaries:
            continue

        txns = []
        if pattern_type == "layering":
            txns = generate_layering(origin_acct, intermediaries, start_date, end_date, known_accounts)

        elif pattern_type == "circular":
            txns = generate_circular(origin_acct, intermediaries, start_date, end_date, known_accounts)

        elif pattern_type == "burst":
            txns = generate_burst(origin_acct, start_date, end_date, known_accounts)

        transactions.extend(txns)

    return transactions


def get_intermediaries(origin, entities, min_count=2):
    potential = [e for e in entities if e.id != origin.id and len(e.accounts) > 0 and e.visibility != "sender"]
    if len(potential) < min_count:
        return None
    return random.sample(potential, min_count)


def generate_layering(origin_acct, intermediaries, start, end, known_accounts):
    txns = []
    chain = [origin_acct] + [random.choice(e.accounts) for e in intermediaries]
    for i in range(len(chain) - 1):
        src, tgt = chain[i], chain[i + 1]
        txn_id = generate_uuid()
        timestamp = generate_timestamp(start, end).strftime("%Y-%m-%d %H:%M:%S")
        amount = round(random.uniform(1000, 5000), 2)
        payment_type = random.choice(["wire", "ach"])
        purpose = "Layering"

        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=src,
            tgt=tgt,
            amount=amount,
            currency="USD",
            payment_type=payment_type,
            is_laundering=True,
            source_description=describe_transaction(payment_type, purpose),
            known_accounts=known_accounts
        )
        txns.extend(entries)
    return txns


def generate_circular(origin_acct, intermediaries, start, end, known_accounts):
    txns = generate_layering(origin_acct, intermediaries, start, end, known_accounts)
    final = intermediaries[-1].accounts[0]
    # Return to origin
    txn_id = generate_uuid()
    timestamp = generate_timestamp(start, end).strftime("%Y-%m-%d %H:%M:%S")
    amount = round(random.uniform(900, 3000), 2)
    payment_type = random.choice(["wire", "ach"])
    purpose = "Circular Flow"

    entries = split_transaction(
        txn_id=txn_id,
        timestamp=timestamp,
        src=final,
        tgt=origin_acct,
        amount=amount,
        currency="USD",
        payment_type=payment_type,
        is_laundering=True,
        source_description=describe_transaction(payment_type, purpose),
        known_accounts=known_accounts
    )
    txns.extend(entries)
    return txns


def generate_burst(origin_acct, start, end, known_accounts, n_bursts=5):
    txns = []
    for _ in range(n_bursts):
        txn_id = generate_uuid()
        timestamp = generate_timestamp(start, end).strftime("%Y-%m-%d %H:%M:%S")
        amount = round(random.uniform(100, 500), 2)
        payment_type = "ach"
        purpose = "Burst Structuring"
        tgt_acct = origin_acct  # Self-directed for simplicity, or random partner

        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=origin_acct,
            tgt=tgt_acct,
            amount=amount,
            currency="USD",
            payment_type=payment_type,
            is_laundering=True,
            source_description=describe_transaction(payment_type, purpose),
            known_accounts=known_accounts
        )
        txns.extend(entries)
    return txns
