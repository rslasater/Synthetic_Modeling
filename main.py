import argparse
import yaml
import sys
import os
from datetime import datetime, timedelta
from random import sample
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generator.entities import generate_entities
from generator.transactions import generate_legit_transactions, generate_profile_transactions
from generator.laundering import generate_laundering_chains
from generator.exporter import export_to_csv, export_to_excel
from generator.labels import propagate_laundering, flag_laundering_accounts
from utils.logger import log
from utils.helpers import earliest_timestamps_by_account

def main():
    parser = argparse.ArgumentParser(description="Synthetic AML Dataset Generator")
    parser.add_argument("--individuals", type=int, default=10, help="Number of individuals")
    parser.add_argument("--companies", type=int, default=5, help="Number of companies")
    parser.add_argument("--banks", type=int, default=3, help="Number of banks")
    parser.add_argument("--legit_txns", type=int, default=500, help="Number of legitimate transactions")
    parser.add_argument("--laundering_chains", type=int, default=10, help="Number of laundering behavior chains")
    parser.add_argument("--patterns", type=str, default=None, help="Path to laundering patterns YAML file")
    parser.add_argument("--agent_profiles", type=str, default=None, help="Path to agent profiles Excel file")
    parser.add_argument("--output", type=str, default="data/aml_dataset.xlsx", help="Output file path")
    parser.add_argument("--format", type=str, choices=["csv", "xlsx"], default="xlsx", help="Export format")
    parser.add_argument("--known_account_ratio", type=float, default=0.5, help="Fraction of accounts with full visibility")
    parser.add_argument("--start_date", type=str, default="2025-01-01", help="Start date for transaction range")
    parser.add_argument("--end_date", type=str, default="2025-01-31", help="End date for transaction range")

    args = parser.parse_args()

    log("🔧 Generating entities...")
    entities_data = generate_entities(
        n_banks=args.banks,
        n_individuals=args.individuals,
        n_companies=args.companies,
        profile_path=args.agent_profiles,
    )
    accounts = entities_data["accounts"]
    entities = entities_data["entities"]

    log(f"🔢 Total accounts generated: {len(accounts)}")

    n_known_accounts = max(1, int(len(accounts) * args.known_account_ratio))
    known_accounts = sample(accounts, n_known_accounts)
    known_accounts_set = set(a.id for a in known_accounts)

    log(f"🔍 Selected known accounts: {len(known_accounts_set)}")

    legit_txns = []

    if args.agent_profiles:
        log(f"📂 Loading agent profiles from {args.agent_profiles}")
        profile_df = pd.read_excel(args.agent_profiles, sheet_name="Combined_Data")
        bank_lookup = {
            str(b.code): {
                "name": b.name,
                "swift_code": b.swift_code,
                "routing_number": b.aba_routing_number,
            }
            for b in entities_data["banks"]
        }
        profile_txns = generate_profile_transactions(
            profile_df=profile_df,
            start_date=args.start_date,
            end_date=args.end_date,
            bank_lookup=bank_lookup,
        )
        legit_txns.extend(profile_txns)
        log(f"✅ Profile-based transactions generated: {len(profile_txns)}")

    if args.legit_txns > 0:
        if args.agent_profiles:
            log("📊 Generating additional legitimate transactions...")
        else:
            log("📊 Generating legitimate transactions...")
        base_txns = generate_legit_transactions(
            accounts=accounts,
            entities=entities,
            n=args.legit_txns,
            start_date=args.start_date,
            end_date=args.end_date,
            known_accounts=known_accounts_set
        )
        legit_txns.extend(base_txns)
        log(f"✅ Legitimate transactions generated: {len(base_txns)}")

    # Determine earliest legitimate timestamp per account
    accounts_set = {a.id for a in accounts}
    earliest_map_all = earliest_timestamps_by_account(legit_txns)
    earliest_map = {aid: ts for aid, ts in earliest_map_all.items() if aid in accounts_set}
    min_start_times = {aid: ts + timedelta(hours=1) for aid, ts in earliest_map.items()}
    accounts_with_history = [a for a in accounts if a.id in earliest_map]

    laundering_txns = []

    if (args.patterns or args.laundering_chains > 0) and not accounts_with_history:
        log("⚠️  No legitimate transaction history; skipping laundering generation")

    # ✅ Pattern-based laundering injection (YAML-driven)
    elif args.patterns:
        log(f"📂 Loading laundering patterns from {args.patterns}")
        with open(args.patterns, "r") as f:
            pattern_config = yaml.safe_load(f)

        from generator.patterns import inject_patterns
        laundering_txns = inject_patterns(
            accounts=accounts_with_history,
            pattern_config=pattern_config,
            known_accounts=known_accounts_set,
            min_start_time=min_start_times,
        )
        log(f"✅ Laundering transactions generated (pattern-based): {len(laundering_txns)}")

    # Optional: Keep chain-based option active if needed
    elif args.laundering_chains > 0:
        log("💸 Generating laundering transaction chains...")
        laundering_txns = generate_laundering_chains(
            entities=entities,
            accounts=accounts_with_history,
            known_accounts=known_accounts_set,
            start_date=datetime.strptime(args.start_date, "%Y-%m-%d"),
            end_date=datetime.strptime(args.end_date, "%Y-%m-%d"),
            n_chains=args.laundering_chains,
            min_start_time=min_start_times,
        )
        log(f"✅ Laundering transactions generated (chains): {len(laundering_txns)}")

    if laundering_txns:
        flag_laundering_accounts(laundering_txns, accounts, entities)

    log("🔍 Propagating laundering labels (taint tracking)...")
    all_txns = legit_txns + laundering_txns
    all_txns = propagate_laundering(all_txns)

    log(f"💾 Exporting {len(all_txns)} transactions to {args.output}")
    if args.format == "csv":
        export_to_csv(all_txns, args.output)
    else:
        export_to_excel(all_txns, args.output)

    log(f"📦 Total transactions to export: {len(all_txns)}")
    log("✅ Done.")

if __name__ == "__main__":
    main()
