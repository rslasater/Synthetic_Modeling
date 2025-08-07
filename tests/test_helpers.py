import os
import sys
from types import SimpleNamespace

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.helpers import split_transaction


def test_split_transaction_amounts_are_absolute():
    src = SimpleNamespace(
        id="A",
        bank_name="Bank",
        owner_name="Alice",
        owner_type="Individual",
        bank="001",
        bank_code="001",
        launderer=False,
    )
    tgt = SimpleNamespace(
        id="B",
        bank_name="Bank",
        owner_name="Bob",
        owner_type="Individual",
        bank="001",
        bank_code="001",
        launderer=False,
    )

    entries = split_transaction(
        txn_id="T1",
        timestamp="2025-01-01 10:00:00",
        src=src,
        tgt=tgt,
        amount=-123.45,
        currency="USD",
        payment_type="ach",
        is_laundering=False,
        known_accounts={"A", "B"},
    )

    assert all(e["amount"] >= 0 for e in entries)
