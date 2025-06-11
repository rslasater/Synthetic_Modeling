import uuid
import random
from datetime import datetime, timedelta, date
from faker import Faker

fake = Faker()

# Track check numbers issued per payor account
CHECK_COUNTERS: dict[str, int] = {}

def next_check_number(payor_id: str) -> int:
    """Return the next sequential 4-digit check number for ``payor_id``."""
    current = CHECK_COUNTERS.get(payor_id)
    if current is None:
        current = random.randint(1000, 9999)
    else:
        current += 1
    CHECK_COUNTERS[payor_id] = current
    return current

def generate_uuid(length=12):
    """Generate a short unique ID (default 12 characters)."""
    return str(uuid.uuid4()).replace('-', '')[:length]

def generate_card_number() -> str:
    """Return a masked Visa or MasterCard number.

    The number is formatted as ``VSXXXX XXXX XXXX ####`` or
    ``MCXXXX XXXX XXXX ####`` where only the last four digits are
    randomly generated.
    """
    brand = random.choice(["VS", "MC"])
    last4 = "".join(str(random.randint(0, 9)) for _ in range(4))
    return f"{brand}XXXX XXXX XXXX {last4}"

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

def suggest_transaction_type(naics_code: str | int | None, payor_type: str | None) -> str:
    """Return a suggested transaction purpose based on ``naics_code``.
    
    This helper maps broad NAICS code prefixes to human readable purchase categories.
    """
    code = str(naics_code or "")

    mapping = [
        (("11",), ["Agricultural Purchase", "Farm Supply", "Crop Service"]),
        (("21",), ["Mining Service", "Resource Extraction", "Mineral Purchase"]),
        (("22",), ["Utility Payment", "Utility Service"]),
        (("23",), ["Construction Service", "Building Project", "Renovation"]),
        (("31", "32", "33"), ["Manufacturing Purchase", "Industrial Goods", "Factory Service"]),
        (("42",), ["Wholesale Purchase", "Bulk Goods", "Wholesale Distribution"]),
        (("722",), ["Restaurant Meal", "Dining Out", "Food Service"]),
        (("445",), ["Grocery Purchase", "Food Shopping", "Supermarket Visit"]),
        (("44", "45"), ["Retail Purchase", "Shopping Trip", "Retail Goods"]),
        (("611",), ["Educational Service", "Tuition Payment", "Course Enrollment"]),
        (("62",), ["Medical Payment", "Healthcare Expense", "Medical Service"]),
        (("52",), ["Financial Service Fee", "Banking Charge"]),
        (("53",), ["Real Estate Payment", "Property Management Fee"]),
        (("54",), ["Professional Service Fee", "Consulting Expense"]),
        (("56",), ["Administrative Service", "Office Expense"]),
        (("61",), ["Educational Expense", "Training Course"]),
        (("71",), ["Entertainment Expense", "Leisure Activity"]),
        (("72",), ["Travel Expense", "Lodging Cost"]),
        (("81",), ["Repair Service", "Maintenance Cost"]),
        (("92",), ["Public Administration Fee", "Government Service"]),
        (("99",), ["Miscellaneous Expense", "Other Services"]),
    ]

    for prefixes, options in mapping:
        if any(code.startswith(p) for p in prefixes):
            return random.choice(options)

    return "Expense"

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

def round_cash_amount(amount: float) -> int:
    """Round a cash amount to the nearest $20 as an integer."""
    return int(round(float(amount) / 20.0)) * 20

def split_transaction(
    txn_id,
    timestamp,
    src,
    tgt,
    amount,
    currency,
    payment_type,
    is_laundering,
    source_description="",
    transaction_type=None,
    known_accounts=None,
    post_date=None,
    atm_id=None,
    atm_location=None,
    channel="ATM",
):
    """Split a transaction into debit and credit entries."""
    known_accounts = known_accounts or set()
    rows = []

    src_known = src is not None and hasattr(src, "id") and src.id in known_accounts
    tgt_known = tgt is not None and hasattr(tgt, "id") and tgt.id in known_accounts

    src_name = getattr(src, "owner_name", fake.name()) if src is not None else ""
    tgt_name = getattr(tgt, "owner_name", None)
    if not tgt_name:
        if hasattr(tgt, "owner_type") and tgt.owner_type in ["Company", "Merchant"]:
            tgt_name = fake.company()
        else:
            tgt_name = fake.name()

    credit_description = source_description or f"{payment_type.upper()} - {tgt_name}"
    debit_description = source_description or f"{payment_type.upper()} - {tgt_name}"
    wire_details = None

    # Custom descriptions for card/POS transactions
    pt_lower = payment_type.lower().replace("_", " ")
    card_aliases = {"credit card", "ccard", "credit"}
    debit_aliases = {"debit card", "debit"}
    if pt_lower in card_aliases | debit_aliases | {"pos"} and src is not None and tgt is not None:
        card_num = getattr(src, "credit_card_number", None)
        if pt_lower in debit_aliases:
            card_num = getattr(src, "debit_card_number", card_num)
        date_str = timestamp.split(" ")[0]
        method = getattr(tgt, "receiving_method", "")
        debit_description = f"{method} - {tgt_name}, {card_num}, {date_str}, {abs(amount):.2f}"
        credit_description = f"{method} - {src_name}, {card_num}, {date_str}, {abs(amount):.2f}"

    if payment_type.lower() == "wire":
        debit_description = credit_description = (
            f"WIRE - Originator: {src_name} Beneficiary: {tgt_name}"
        )
        is_international = (
            (src is not None and getattr(src, "country", "United States") != "United States")
            or (tgt is not None and getattr(tgt, "country", "United States") != "United States")
        )
        wire_details = {
            "swift_code": getattr(src, "swift_code", ""),
            "routing_number": getattr(src, "routing_number", ""),
            "is_international": is_international,
        }
        if is_international:
            wire_details["exchange_rate"] = round(random.uniform(0.8, 1.2), 4)

    if payment_type.lower() == "ach" and src is not None and tgt is not None:
        sec_code = "PPD"
        if src.owner_type == "Company" and tgt.owner_type in ["Company", "Merchant"]:
            sec_code = "CCD"

        debit_description = (
            f"ACH Debit - Bill Payment, {tgt_name}, SEC-Code: {sec_code}, Settled"
        )
        credit_description = (
            f"ACH Credit - Originator: {src_name}, SEC-Code: {sec_code}, Settled"
        )

    if payment_type.lower() == "check" and src is not None and tgt is not None:
        check_num = next_check_number(src.id)
        txn_type = transaction_type or suggest_transaction_type(None, getattr(src, "owner_type", None))
        debit_description = (
            f"Check - {tgt_name}, {check_num:04d}, {txn_type}, {abs(amount):.2f}, Settled"
        )
        credit_description = (
            f"Check - {src_name}, {src.id}, {getattr(src, 'routing_number', '')}, {abs(amount):.2f}, Settled"
        )

    if payment_type.lower() == "cash":
        if channel == "ATM":
            amount = round_cash_amount(amount)
        # Use provided ATM/BEnt metadata if available
        if atm_id is None:
            atm_id = generate_uuid(8)
        if atm_location is None:
            atm_name = fake.company()
            atm_address = fake.address().replace("\n", ", ")
            atm_location = f"{atm_name} ({atm_address})"

        credit_description = f"CASH - Deposit at {atm_location}"
        debit_description = f"CASH - Withdrawal at {atm_location}"

        placeholder_cp = channel

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
                    "bank_name": tgt.bank_name,
                    "owner_name": tgt.owner_name,
                    "payment_type": payment_type,
                    "is_laundering": is_laundering,
                    "source_description": credit_description,
                    "post_date": post_date,
                    "atm_id": atm_id,
                    "atm_location": atm_location,
                    "wire_details": wire_details,
                    "channel": channel
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
                    "bank_name": src.bank_name,
                    "owner_name": src.owner_name,
                    "payment_type": payment_type,
                    "is_laundering": is_laundering,
                    "source_description": debit_description,
                    "post_date": post_date,
                    "atm_id": atm_id,
                    "atm_location": atm_location,
                    "wire_details": wire_details,
                    "channel": channel
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
                "bank_name": src.bank_name,
                "owner_name": src.owner_name,
                "payment_type": payment_type,
                "is_laundering": is_laundering,
                "source_description": debit_description,
                "post_date": post_date,
                "atm_id": atm_id,
                "atm_location": atm_location,
                "wire_details": wire_details,
                "channel": channel
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
                "bank_name": tgt.bank_name,
                "owner_name": tgt.owner_name,
                "payment_type": payment_type,
                "is_laundering": is_laundering,
                "source_description": credit_description,
                "post_date": post_date,
                "atm_id": atm_id,
                "atm_location": atm_location,
                "wire_details": wire_details,
                "channel": channel
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
            "bank_name": src.bank_name,
            "owner_name": src.owner_name,
            "payment_type": payment_type,
            "is_laundering": is_laundering,
            "source_description": debit_description,
            "post_date": post_date,
            "wire_details": wire_details
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
            "bank_name": tgt.bank_name,
            "owner_name": tgt.owner_name,
            "payment_type": payment_type,
            "is_laundering": is_laundering,
            "source_description": credit_description,
            "post_date": post_date,
            "wire_details": wire_details
        })

    if payment_type.lower() == "wire" and src_known:
        rows.append({
            "transaction_id": txn_id,
            "entry_id": txn_id + "-F",
            "timestamp": timestamp,
            "account_id": src.id,
            "counterparty": "",
            "amount": -25.0,
            "direction": "debit",
            "currency": currency,
            "bank_name": src.bank_name,
            "owner_name": src.owner_name,
            "payment_type": "fee",
            "is_laundering": is_laundering,
            "source_description": "Wire Transfer Fee",
            "post_date": post_date,
            "wire_details": None
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


def is_us_federal_holiday(dt: datetime) -> bool:
    """Return True if the given date falls on a US federal holiday (2025)."""
    holidays_2025 = {
        (1, 1),   # New Year's Day
        (1, 20),  # Martin Luther King Jr. Day
        (2, 17),  # Washington's Birthday
        (5, 26),  # Memorial Day
        (7, 4),   # Independence Day
        (9, 1),   # Labor Day
        (10, 13), # Columbus Day
        (11, 11), # Veterans Day
        (11, 27), # Thanksgiving Day
        (12, 25), # Christmas Day
    }
    return (dt.month, dt.day) in holidays_2025


def generate_post_date(transaction_dt: datetime) -> datetime:
    """Return a posting datetime after ``transaction_dt`` within business hours."""

    for _ in range(100):
        # Try an offset between 0 and 3 days
        post_dt = transaction_dt + timedelta(days=random.randint(0, 3))

        # If the tentative date falls on a weekend, move to the following Monday
        if post_dt.weekday() >= 5:
            post_dt += timedelta(days=7 - post_dt.weekday())

        # Skip US federal holidays
        while is_us_federal_holiday(post_dt):
            post_dt += timedelta(days=1)

        # Ensure we don't exceed the three-day window
        if (post_dt - transaction_dt).days > 3:
            continue

        # Choose a posting time within banking hours
        start_hour = 8
        if post_dt.date() == transaction_dt.date():
            start_hour = max(start_hour, transaction_dt.hour)
        if start_hour >= 17:
            # No business hours remaining on this day
            continue
        hour = random.randint(start_hour, 16)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        post_dt = post_dt.replace(hour=hour, minute=minute, second=second, microsecond=0)

        # Verify ordering
        if post_dt > transaction_dt:
            return post_dt

    # Fallback: next business day at 09:00
    post_dt = transaction_dt + timedelta(days=1)
    post_dt = post_dt.replace(hour=9, minute=0, second=0, microsecond=0)
    while post_dt.weekday() >= 5 or is_us_federal_holiday(post_dt):
        post_dt += timedelta(days=1)
    return post_dt


def generate_transaction_timestamp(start_dt: datetime, end_dt: datetime,
                                   entity_type: str | None = None,
                                   override_hours: bool = False) -> datetime:
    """Generate a transaction timestamp honoring business hour rules."""
    for _ in range(100):
        ts = random_timestamp(start_dt, end_dt)
        if override_hours:
            return ts

        if entity_type == "Company":
            if ts.weekday() < 5 and 8 <= ts.hour < 17:
                return ts
        else:  # Person or other
            if 8 <= ts.hour < 20:
                return ts

    return ts  # fallback if conditions not met
