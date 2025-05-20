from collections import defaultdict

def propagate_laundering(transactions):
    """
    Mark transactions as laundering if they receive tainted funds from a laundering source.
    This is a one-pass, forward-only propagation based on transaction order.
    """

    tainted_accounts = set()
    updated_transactions = []

    for txn in transactions:
        source = txn["source_account"]
        target = txn["target_account"]

        # If laundering or from a tainted source, label it and mark target as tainted
        if txn["is_laundering"] or source in tainted_accounts:
            txn["is_laundering"] = True
            tainted_accounts.add(target)

        updated_transactions.append(txn)

    return updated_transactions
