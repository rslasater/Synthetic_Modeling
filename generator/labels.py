from collections import defaultdict
from datetime import datetime

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
    """Propagate laundering labels through debit → credit flow.

    Only transactions that occur *after* an account engages in laundering
    activity should be marked as laundering. Legitimate history before the first
    laundering transaction remains untouched.
    """

    # Track the earliest laundering timestamp for each account
    taint_start: dict[str, datetime | None] = defaultdict(lambda: None)

    for entry in entries:
        if entry.get("is_laundering", False):
            ts = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
            acct = entry["account_id"]
            if taint_start[acct] is None or ts < taint_start[acct]:
                taint_start[acct] = ts

    updated_entries = []

    for entry in entries:
        ts = datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S")
        acct = entry.get("account_id")
        counterparty = entry.get("counterparty")
        direction = entry.get("direction")

        acct_start = taint_start.get(acct)
        cp_start = taint_start.get(counterparty)

        if entry.get("is_laundering", False):
            updated_entries.append(entry)
            continue

        # Mark credits from tainted counterparties that occur after taint start
        if direction == "credit" and cp_start and ts >= cp_start:
            taint_start.setdefault(acct, ts)

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
