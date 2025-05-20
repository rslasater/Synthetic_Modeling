import argparse
import yaml
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from generator.entities import generate_entities
from generator.transactions import generate_legit_transactions
from generator.patterns import inject_patterns
from generator.labels import propagate_laundering
from generator.exporter import export_to_csv, export_to_excel
from utils.logger import log

def main():
    parser = argparse.ArgumentParser(description="Synthetic AML Dataset Generator")
    parser.add_argument("--individuals", type=int, default=10, help="Number of individuals")
    parser.add_argument("--companies", type=int, default=5, help="Number of companies")
    parser.add_argument("--banks", type=int, default=3, help="Number of banks")
    parser.add_argument("--legit_txns", type=int, default=500, help="Number of legitimate transactions")
    parser.add_argument("--patterns", type=str, default="config/patterns.yaml", help="Path to laundering patterns YAML")
    parser.add_argument("--output", type=str, default="data/aml_dataset.xlsx", help="Output file path")
    parser.add_argument("--format", type=str, choices=["csv", "xlsx"], default="xlsx", help="Export format")
    args = parser.parse_args()

    log("🔧 Generating entities...")
    entities = generate_entities(n_banks=args.banks, n_individuals=args.individuals, n_companies=args.companies)
    accounts = entities["accounts"]

    log("📊 Generating legitimate transactions...")
    legit_txns = generate_legit_transactions(accounts, n=args.legit_txns)

    log(f"📂 Loading laundering patterns from {args.patterns}")
    with open(args.patterns, "r") as f:
        pattern_config = yaml.safe_load(f)

    log("💸 Injecting laundering patterns...")
    laundering_txns = inject_patterns(accounts, pattern_config)

    log("🔍 Propagating laundering labels (taint tracking)...")
    all_txns = legit_txns + laundering_txns
    all_txns = propagate_laundering(all_txns)

    log(f"💾 Exporting {len(all_txns)} transactions to {args.output}")
    if args.format == "csv":
        export_to_csv(all_txns, args.output)
    else:
        export_to_excel(all_txns, args.output)

    log("✅ Done.")

if __name__ == "__main__":
    main()
