import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generator.labels import propagate_laundering


def test_propagate_laundering_respects_first_event():
    entries = [
        {
            "timestamp": "2025-01-01 09:00:00",
            "account_id": "A",
            "counterparty": "B",
            "direction": "debit",
            "is_laundering": False,
        },
        {
            "timestamp": "2025-01-02 10:00:00",
            "account_id": "A",
            "counterparty": "C",
            "direction": "debit",
            "is_laundering": True,
        },
        {
            "timestamp": "2025-01-03 11:00:00",
            "account_id": "D",
            "counterparty": "A",
            "direction": "credit",
            "is_laundering": False,
        },
        {
            "timestamp": "2025-01-04 12:00:00",
            "account_id": "E",
            "counterparty": "A",
            "direction": "credit",
            "is_laundering": False,
        },
    ]

    result = propagate_laundering(entries)

    assert result[0]["is_laundering"] is False
    assert result[1]["is_laundering"] is True
    assert result[2]["is_laundering"] is True
    assert result[3]["is_laundering"] is True
