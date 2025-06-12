from collections import defaultdict

def flag_laundering_accounts(entries, accounts, entities=None):
    """Mark Account and Entity objects participating in laundering."""
    laundering_ids = {e["account_id"] for e in entries if e.get("is_laundering")}
    acct_map = {a.id: a for a in accounts}

    for acct_id in laundering_ids:
        acct = acct_map.get(acct_id)
        if not acct:
            continue
        acct.launderer = True
        if entities is not None:
            for ent in entities:
                if acct in getattr(ent, "accounts", []):
                    ent.launderer = True

def propagate_laundering(entries):
    """Propagate laundering labels based on transaction chronology.

    Only transactions that occur **after** an account's first laundering event
    are marked. Entries are processed in timestamp order to ensure proper
    propagation.
    """

    from datetime import datetime

    # Sort entries chronologically to track first laundering occurrence
    sorted_entries = sorted(
        entries, key=lambda e: e.get("timestamp")
    )

    tainted_accounts: set[str] = set()
    first_seen: dict[str, datetime] = {}
    updated: list[dict] = []

    for entry in sorted_entries:
        ts_raw = entry.get("timestamp")
        ts = (
            datetime.strptime(ts_raw, "%Y-%m-%d %H:%M:%S")
            if isinstance(ts_raw, str)
            else ts_raw
        )
        acct = entry.get("account_id")
        counterparty = entry.get("counterparty")
        direction = entry.get("direction")

        if entry.get("is_laundering", False):
            tainted_accounts.add(acct)
            first_seen.setdefault(acct, ts)

        if (
            direction == "credit"
            and counterparty in tainted_accounts
            and ts >= first_seen[counterparty]
        ):
            entry["is_laundering"] = True
            tainted_accounts.add(acct)
            first_seen.setdefault(acct, ts)

        if (
            direction == "debit"
            and acct in tainted_accounts
            and ts >= first_seen[acct]
        ):
            entry["is_laundering"] = True
            tainted_accounts.add(counterparty)
            first_seen.setdefault(counterparty, ts)

        updated.append(entry)

    # Return entries sorted to maintain chronological order
    return sorted(updated, key=lambda e: e.get("timestamp"))
