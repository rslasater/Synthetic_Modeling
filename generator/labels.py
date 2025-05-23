from collections import defaultdict

def propagate_laundering(entries):
    """
    Propagate laundering labels through debit → credit flow.
    Assumes double-entry format with 'account_id', 'counterparty', and 'direction'.
    """
    tainted_accounts = set()
    updated_entries = []

    # First pass — mark tainted accounts directly
    for entry in entries:
        if entry.get("is_laundering", False):
            tainted_accounts.add(entry["account_id"])

    # Second pass — propagate taint based on flow direction
    for entry in entries:
        direction = entry.get("direction")
        acct = entry.get("account_id")
        counterparty = entry.get("counterparty")

        # If the counterparty is tainted and this account is the recipient, mark it
        if direction == "credit" and counterparty in tainted_accounts:
            tainted_accounts.add(acct)
            entry["is_laundering"] = True

        # If this is a tainted debit, make sure the counterparty becomes tainted too
        if direction == "debit" and acct in tainted_accounts:
            tainted_accounts.add(counterparty)
            entry["is_laundering"] = True

        updated_entries.append(entry)

    return updated_entries
