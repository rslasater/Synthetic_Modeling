import uuid
import random
from datetime import datetime, timedelta, date

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

def split_transaction(txn_id, timestamp, src, tgt, amount, currency, payment_type, is_laundering, source_description=""):
    rows = []

    if payment_type == "cash":
        # One-sided credit for cash deposit
        rows.append({
            "entry_id": txn_id,
            "timestamp": timestamp,
            "account_id": tgt.id,
            "counterparty": "",
            "amount": amount,  # Positive
            "direction": "credit",
            "currency": currency,
            "payment_type": payment_type,
            "is_laundering": is_laundering,
            "source_description": source_description
        })
    else:
        # Debit from source (amount is negative)
        rows.append({
            "entry_id": txn_id + "-D",
            "timestamp": timestamp,
            "account_id": src.id,
            "counterparty": tgt.id,
            "amount": -abs(amount),  # Force negative
            "direction": "debit",
            "currency": currency,
            "payment_type": payment_type,
            "is_laundering": is_laundering,
            "source_description": source_description
        })
        # Credit to target (amount is positive)
        rows.append({
            "entry_id": txn_id + "-C",
            "timestamp": timestamp,
            "account_id": tgt.id,
            "counterparty": src.id,
            "amount": abs(amount),  # Force positive
            "direction": "credit",
            "currency": currency,
            "payment_type": payment_type,
            "is_laundering": is_laundering,
            "source_description": source_description
        })

    return rows

def generate_timestamp(start_date, end_date):
    """
    Generate a random timestamp between two datetime objects.
    """
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start_date + timedelta(seconds=random_seconds)
