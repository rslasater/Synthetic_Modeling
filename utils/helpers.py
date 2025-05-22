import uuid
import random
from datetime import datetime, timedelta, date
from faker import Faker

fake = Faker()

def generate_uuid(length=12):
    """Generate a short unique ID (default 12 characters)."""
    return str(uuid.uuid4()).replace('-', '')[:length]

def parse_date(date_str):
    """Parse a date string like '2025-01-01' into a datetime object."""
    return datetime.strptime(date_str, "%Y-%m-%d")

def random_timestamp(start_date, end_date):
    """Generate a random timestamp between two datetime objects."""
    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start_date + timedelta(seconds=random_seconds)

def safe_sample(population, k):
    """Safely sample k items from a list, even if the list is smaller than k."""
    return random.sample(population, min(k, len(population)))

def to_datetime(value):
    """
    Convert a value to a datetime object.
    Accepts either a string ("YYYY-MM-DD") or a datetime.date object.
    """
    if isinstance(value, datetime):
        return value
    elif isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    elif isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d")
    else:
        raise TypeError(f"Unsupported type for to_datetime: {type(value)}")

def split_transaction(txn_id, timestamp, src, tgt, amount, currency, payment_type, is_laundering,
                      source_description="", known_accounts=None):
    known_accounts = known_accounts or set()
    rows = []

    src_known = src is not None and hasattr(src, "id") and src.id in known_accounts
    tgt_known = tgt is not None and hasattr(tgt, "id") and tgt.id in known_accounts

    # Dynamically name destination based on target account owner_type
    if hasattr(tgt, "owner_type"):
        if tgt.owner_type == "Person":
            recipient_name = fake.name()
        elif tgt.owner_type == "Company":
            recipient_name = fake.company()
        else:
            recipient_name = fake.name()
    else:
        recipient_name = fake.name()

    credit_description = f"{payment_type.upper()} - {recipient_name}"
    debit_description = f"{payment_type.upper()} - {recipient_name}"

    if payment_type.lower() == "cash":
        # Simulated ATM metadata
        atm_name = fake.company()
        atm_address = fake.address().replace("\n", ", ")
        atm_id = generate_uuid(8)
        credit_description = f"CASH - Deposit at {atm_name} ATM ({atm_address})"
        debit_description = f"CASH - Withdrawal at {atm_name} ATM ({atm_address})"

        placeholder_cp = "ATM"

        # Deposit: src is None
        if src is None and tgt is not None:
            if tgt_known:
                rows.append({
                    "transaction_id": txn_id,
                    "entry_id": txn_id + "-C",
                    "timestamp": timestamp,
                    "account_id": tgt.id,
                    "counterparty": placeholder_cp,
                    "amount": abs(amount),
                    "direction": "credit",
                    "currency": currency,
                    "payment_type": payment_type,
                    "is_laundering": is_laundering,
                    "source_description": credit_description,
                    "atm_id": atm_id,
                    "atm_location": atm_address
                })
            return rows

        # Withdrawal: tgt is None
        if tgt is None and src is not None:
            if src_known:
                rows.append({
                    "transaction_id": txn_id,
                    "entry_id": txn_id + "-D",
                    "timestamp": timestamp,
                    "account_id": src.id,
                    "counterparty": placeholder_cp,
                    "amount": -abs(amount),
                    "direction": "debit",
                    "currency": currency,
                    "payment_type": payment_type,
                    "is_laundering": is_laundering,
                    "source_description": debit_description,
                    "atm_id": atm_id,
                    "atm_location": atm_address
                })
            return rows

        # Traditional cash transfer between two accounts (rare)
        if src_known:
            rows.append({
                "transaction_id": txn_id,
                "entry_id": txn_id + "-D",
                "timestamp": timestamp,
                "account_id": src.id,
                "counterparty": tgt.id if tgt else placeholder_cp,
                "amount": -abs(amount),
                "direction": "debit",
                "currency": currency,
                "payment_type": payment_type,
                "is_laundering": is_laundering,
                "source_description": debit_description,
                "atm_id": atm_id,
                "atm_location": atm_address
            })

        if tgt_known:
            rows.append({
                "transaction_id": txn_id,
                "entry_id": txn_id + "-C",
                "timestamp": timestamp,
                "account_id": tgt.id,
                "counterparty": src.id if src else placeholder_cp,
                "amount": abs(amount),
                "direction": "credit",
                "currency": currency,
                "payment_type": payment_type,
                "is_laundering": is_laundering,
                "source_description": credit_description,
                "atm_id": atm_id,
                "atm_location": atm_address
            })

        return rows

    # Non-cash transactions
    if src_known:
        rows.append({
            "transaction_id": txn_id,
            "entry_id": txn_id + "-D",
            "timestamp": timestamp,
            "account_id": src.id,
            "counterparty": tgt.id,
            "amount": -abs(amount),
            "direction": "debit",
            "currency": currency,
            "payment_type": payment_type,
            "is_laundering": is_laundering,
            "source_description": debit_description
        })

    if tgt_known:
        rows.append({
            "transaction_id": txn_id,
            "entry_id": txn_id + "-C",
            "timestamp": timestamp,
            "account_id": tgt.id,
            "counterparty": src.id if src else "",
            "amount": abs(amount),
            "direction": "credit",
            "currency": currency,
            "payment_type": payment_type,
            "is_laundering": is_laundering,
            "source_description": credit_description
        })

    print(f"[DEBUG] src: {src.id if src else 'CASH'}, tgt: {tgt.id if tgt else 'CASH'}, src_known: {src_known}, tgt_known: {tgt_known}")
    if not src_known and not tgt_known:
        print(f"⚠️ Skipping txn {txn_id}: both accounts unknown")

    return rows


def generate_timestamp(start_date, end_date):
    """Generate a random timestamp between two datetime objects."""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start_date + timedelta(seconds=random_seconds)

def describe_transaction(payment_type, purpose=None):
    company = fake.company()
    name = fake.name()
    address = fake.address().replace("\n", ", ")

    if payment_type == "ach":
        return f"ACH - {purpose} from {company} ({address})"
    elif payment_type == "cash":
        direction = "Deposit" if purpose == "Deposit" else "Withdrawal"
        return f"CASH - {direction} at {company} ATM ({address})"
    elif payment_type == "wire":
        return f"WIRE - {purpose} via {company} Bank"
    elif payment_type == "credit_card":
        return f"CREDIT CARD - {purpose} charged to account at {company}"
    elif payment_type == "check":
        return f"CHECK - {purpose} written by {name}"

    return f"{payment_type.upper()} - {purpose or 'Transaction'}"
