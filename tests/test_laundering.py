import random
from datetime import timedelta
import unittest

from generator.entities import generate_entities
from generator.transactions import generate_legit_transactions
from generator.laundering import generate_laundering_chains
from generator.labels import flag_laundering_accounts
from utils.helpers import earliest_timestamps_by_account


class LaunderingTests(unittest.TestCase):
    def test_flagged_accounts_have_legit(self):
        random.seed(0)
        data = generate_entities(n_banks=1, n_individuals=5, n_companies=5)
        accounts = data["accounts"]
        entities = data["entities"]
        known = set(a.id for a in accounts)

        legit = generate_legit_transactions(
            accounts=accounts,
            entities=entities,
            n=50,
            start_date="2025-01-01",
            end_date="2025-01-05",
            known_accounts=known,
        )

        min_map = earliest_timestamps_by_account(legit)
        min_start = {k: v + timedelta(hours=1) for k, v in min_map.items()}
        accounts_hist = [a for a in accounts if a.id in min_map]

        laundering = generate_laundering_chains(
            entities=entities,
            accounts=accounts_hist,
            known_accounts=known,
            start_date=min(min_map.values()),
            end_date=min(min_map.values()) + timedelta(days=1),
            n_chains=2,
            min_start_time=min_start,
        )

        flag_laundering_accounts(laundering, accounts, entities)
        flagged = [a for a in accounts if a.launderer]
        self.assertTrue(flagged)
        for acct in flagged:
            self.assertTrue(
                any(e["account_id"] == acct.id and not e["is_laundering"] for e in legit)
            )


if __name__ == "__main__":
    unittest.main()
