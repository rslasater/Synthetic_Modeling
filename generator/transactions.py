import random
from datetime import datetime, timedelta, date
import calendar

from utils.helpers import (
    generate_uuid,
    generate_transaction_timestamp,
    generate_post_date,
    to_datetime,
    split_transaction,
    describe_transaction,
    fake,
)
import pandas as pd

# Common payment types
PAYMENT_TYPES = ["wire", "credit_card", "ach", "check", "cash"]


class ProfileAccount:
    """Lightweight account object used for profile-driven transactions."""

    def __init__(self, id, owner_id, owner_type, owner_name="", bank_name=""):
        self.id = str(id)
        self.owner_id = owner_id
        self.owner_type = owner_type
        self.owner_name = owner_name
        self.bank_name = bank_name


def first_and_third_mondays(start_dt: datetime, end_dt: datetime) -> list[date]:
    """Return all first and third Mondays between ``start_dt`` and ``end_dt``."""
    dates = []
    current = date(start_dt.year, start_dt.month, 1)
    end_date = end_dt.date()
    while current <= end_date:
        c = calendar.Calendar()
        mondays = [d for d in c.itermonthdates(current.year, current.month)
                   if d.weekday() == 0 and d.month == current.month]
        if mondays:
            first = mondays[0]
            third = mondays[2] if len(mondays) > 2 else None
            if start_dt.date() <= first <= end_date:
                dates.append(first)
            if third and start_dt.date() <= third <= end_date:
                dates.append(third)
        # move to first day of next month
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return dates


def generate_legit_transactions(accounts, entities, n=1000, start_date="2025-01-01", end_date="2025-01-31", known_accounts=None):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    known_accounts = set(known_accounts) if known_accounts else set()

    transactions = []
    attempts = 0
    skipped_visibility = 0
    skipped_known = 0
    skipped_payment_type = 0
    success = 0

    while success < n and attempts < n * 10:  # Avoid infinite loops
        attempts += 1

        # Randomly choose a primary account and its owning entity
        primary_acct = random.choice(accounts)
        primary_entity = next((e for e in entities if e.id == primary_acct.owner_id), None)
        if not primary_entity:
            continue

        sender_rules = primary_entity.get_allowed_transactions()
        if not sender_rules:
            skipped_payment_type += 1
            continue

        payment_type = random.choice(list(sender_rules.keys()))
        purpose = random.choice(sender_rules[payment_type])
        source_description = describe_transaction(payment_type, purpose)

        ts_dt = generate_transaction_timestamp(
            start_dt,
            end_dt,
            entity_type=primary_entity.__class__.__name__,
        )
        timestamp = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
        post_date = generate_post_date(ts_dt).strftime("%Y-%m-%d %H:%M:%S")
        amount = round(random.uniform(50, 5000), 2)
        txn_id = generate_uuid()

        # Determine src/tgt accounts based on payment type
        if payment_type.lower() == "cash":
            deposit = purpose.lower() == "deposit" if purpose else random.choice([True, False])
            if deposit:
                src = None
                tgt = primary_acct
                if tgt.id not in known_accounts:
                    skipped_known += 1
                    continue
                if primary_entity.visibility not in ["receiver", "both"]:
                    skipped_visibility += 1
                    continue
            else:
                src = primary_acct
                tgt = None
                if src.id not in known_accounts:
                    skipped_known += 1
                    continue
                if primary_entity.visibility not in ["sender", "both"]:
                    skipped_visibility += 1
                    continue
        else:
            # Non-cash transfers require two accounts
            src = primary_acct
            tgt = random.choice([a for a in accounts if a.id != src.id])
            tgt_entity = next((e for e in entities if e.id == tgt.owner_id), None)
            if not tgt_entity:
                continue
            if src.id not in known_accounts and tgt.id not in known_accounts:
                skipped_known += 1
                continue
            if primary_entity.visibility not in ["sender", "both"] or tgt_entity.visibility not in ["receiver", "both"]:
                skipped_visibility += 1
                continue

        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=src,
            tgt=tgt,
            amount=amount,
            currency="USD",
            payment_type=payment_type,
            is_laundering=False,
            source_description=source_description,
            known_accounts=known_accounts,
            post_date=post_date
        )

        transactions.extend(entries)
        success += 1

    print(f"[DEBUG] Attempted: {attempts}")
    print(f"[DEBUG] Success: {success}")
    print(f"[DEBUG] Skipped (visibility): {skipped_visibility}")
    print(f"[DEBUG] Skipped (unknown accounts): {skipped_known}")
    print(f"[DEBUG] Skipped (payment type issues): {skipped_payment_type}")

    return transactions


def generate_payroll_transactions(profile_df: pd.DataFrame, start_dt: datetime, end_dt: datetime, known_accounts: set) -> list[dict]:
    """Generate payroll ACH transactions from companies to employees."""
    if "employer" not in profile_df.columns:
        return []

    employees = profile_df[(profile_df["type"] == "person") & profile_df["employer"].notna()]
    companies = profile_df[profile_df["type"] == "company"].set_index("entity_id")
    payroll_dates = first_and_third_mondays(start_dt, end_dt)

    transactions = []

    for _, emp in employees.iterrows():
        employer_id = emp.get("employer")
        if employer_id not in companies.index:
            continue

        employer = companies.loc[employer_id]

        emp_acct_id = emp.get("account_number")
        if pd.isna(emp_acct_id):
            emp_acct_id = emp["entity_id"]
        emp_acct = ProfileAccount(
            id=emp_acct_id,
            owner_id=emp["entity_id"],
            owner_type="Person",
            owner_name=emp.get("name", ""),
        )

        comp_acct_id = employer.get("account_number")
        if pd.isna(comp_acct_id):
            comp_acct_id = employer["entity_id"]
        comp_acct = ProfileAccount(
            id=comp_acct_id,
            owner_id=employer["entity_id"],
            owner_type="Company",
            owner_name=employer.get("name", ""),
        )

        txn_scaler = float(employer.get("transaction_scaler") or 1)
        base = 5000 * txn_scaler
        amount = round(random.uniform(base * 0.9, base * 1.1), 2)

        company_name = employer.get("name", "")
        company_addr = str(employer.get("address", "")).replace("\n", ", ")
        employee_name = emp.get("name", "")

        for pay_date in payroll_dates:
            ts_dt = datetime.combine(pay_date, datetime.min.time())
            ts_dt = ts_dt.replace(hour=random.randint(8, 16), minute=random.randint(0, 59), second=random.randint(0, 59))
            timestamp = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
            post_date = generate_post_date(ts_dt).strftime("%Y-%m-%d %H:%M:%S")
            txn_id = generate_uuid()

            desc = {
                "credit": f"ACH Direct Dep Payroll {company_name} \u2013 {company_addr}",
                "debit": f"ACH Payroll {employee_name} \u2013 {emp_acct_id}",
            }

            entries = split_transaction(
                txn_id=txn_id,
                timestamp=timestamp,
                src=comp_acct,
                tgt=emp_acct,
                amount=amount,
                currency="USD",
                payment_type="ach",
                is_laundering=False,
                source_description=desc,
                known_accounts=known_accounts,
                post_date=post_date,
            )
            transactions.extend(entries)

    return transactions


def generate_profile_transactions(profile_df: pd.DataFrame, start_date: str, end_date: str) -> list[dict]:
    """Generate transactions using structured agent profiles."""
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    known_accounts = set(profile_df["account_number"].dropna().astype(str))

    merchants = profile_df[profile_df["type"] == "merchant"].copy()
    payers = profile_df[profile_df["type"].isin(["person", "company"])]
    bent_df = profile_df[profile_df["type"] == "BEnt"]
    bents_by_bank = {
        str(bank): g[["name", "address"]].to_dict("records")
        for bank, g in bent_df.groupby("bank")
    }

    pending_deposits: dict[str, float] = {}

    transactions = []
    payroll_txns = generate_payroll_transactions(profile_df, start_dt, end_dt, known_accounts)
    transactions.extend(payroll_txns)

    for _, payer in payers.iterrows():
        patterns = payer.get("merchant_patterns")
        freqs = payer.get("merchant_frequency")
        if not isinstance(patterns, str) or not isinstance(freqs, str):
            continue

        pattern_list = [p.strip() for p in patterns.split(',') if p.strip()]
        freq_list = [float(f.strip()) for f in freqs.split(',') if f.strip()]
        if not pattern_list or not freq_list:
            continue

        txn_scaler = float(payer.get("transaction_scaler") or 1)
        payer_acct_id = payer.get("account_number")
        if pd.isna(payer_acct_id):
            payer_acct_id = payer["entity_id"]
        payer_acct = ProfileAccount(
            id=payer_acct_id,
            owner_id=payer["entity_id"],
            owner_type=payer["type"].capitalize(),
            owner_name=payer.get("name", "")
        )

        for code, freq in zip(pattern_list, freq_list):
            try:
                freq_val = float(freq)
            except ValueError:
                continue
            num_txns = max(1, int(round(freq_val)))

            eligible = merchants[merchants["naics_code"].astype(str).str.startswith(str(int(float(code)) if code.strip().replace('.', '', 1).isdigit() else code))]
            if eligible.empty:
                continue

            for _ in range(num_txns):
                merchant = eligible.sample(1).iloc[0]
                tgt_acct_id = merchant.get("account_number")
                if pd.isna(tgt_acct_id):
                    tgt_acct_id = merchant["entity_id"]
                tgt_acct = ProfileAccount(
                    id=tgt_acct_id,
                    owner_id=merchant["entity_id"],
                    owner_type="Merchant",
                    owner_name=merchant.get("name", "")
                )

                pay_opts = merchant.get("accepted_payment_methods")
                if isinstance(pay_opts, str) and pay_opts.strip():
                    payment_types = [p.strip().lower() for p in pay_opts.split(',') if p.strip()]
                else:
                    payment_types = PAYMENT_TYPES
                payment_type = random.choice(payment_types)

                avg_exp = merchant.get("average_expense")
                if pd.isna(avg_exp):
                    avg_exp = 100.0
                amount = random.uniform(avg_exp * 0.85, avg_exp * 1.15)
                amount *= txn_scaler

                ts_dt = generate_transaction_timestamp(start_dt, end_dt, entity_type=payer_acct.owner_type)
                timestamp = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
                post_date = generate_post_date(ts_dt).strftime("%Y-%m-%d %H:%M:%S")
                txn_id = generate_uuid()

                amount = round(amount, 2)

                if payment_type == "cash":
                    # Withdrawal by payer via BEnt
                    payer_bank = str(payer.get("bank"))
                    payer_bents = bents_by_bank.get(payer_bank, [])
                    if payer_bents:
                        bent = random.choice(payer_bents)
                        bent_id = bent.get("name")
                        bent_loc = bent.get("address")
                    else:
                        bent_id = generate_uuid(8)
                        bent_loc = fake.address().replace("\n", ", ")

                    entries = split_transaction(
                        txn_id=txn_id + "W",
                        timestamp=timestamp,
                        src=payer_acct,
                        tgt=None,
                        amount=amount,
                        currency="USD",
                        payment_type="cash",
                        is_laundering=False,
                        known_accounts=known_accounts,
                        post_date=post_date,
                        atm_id=bent_id,
                        atm_location=bent_loc

                    )
                    transactions.extend(entries)

                    deposit_now = random.choice([True, False])
                    if deposit_now:
                        merch_bank = str(merchant.get("bank"))
                        merch_bents = bents_by_bank.get(merch_bank, [])
                        if merch_bents:
                            bent2_rec = random.choice(merch_bents)
                            bent2 = bent2_rec.get("name")
                            bent2_loc = bent2_rec.get("address")
                        else:
                            bent2 = generate_uuid(8)
                            bent2_loc = fake.address().replace("\n", ", ")

                        entries = split_transaction(
                            txn_id=txn_id + "D",
                            timestamp=timestamp,
                            src=None,
                            tgt=tgt_acct,
                            amount=amount,
                            currency="USD",
                            payment_type="cash",
                            is_laundering=False,
                            known_accounts=known_accounts,
                            post_date=post_date,
                            atm_id=bent2,
                            atm_location=bent2_loc,
                        )
                        transactions.extend(entries)
                    else:
                        pending_deposits[tgt_acct.id] = pending_deposits.get(tgt_acct.id, 0) + amount
                else:
                    entries = split_transaction(
                        txn_id=txn_id,
                        timestamp=timestamp,
                        src=payer_acct,
                        tgt=tgt_acct,
                        amount=amount,
                        currency="USD",
                        payment_type=payment_type,
                        is_laundering=False,
                        source_description=describe_transaction(payment_type, "Purchase"),
                        known_accounts=known_accounts,
                        post_date=post_date
                    )
                    transactions.extend(entries)

    # Batch deposit accumulated cash for merchants/companies
    for acct_id, amt in pending_deposits.items():
        merchant_row = merchants[merchants["account_number"] == acct_id]
        if merchant_row.empty:
            continue
        merchant = merchant_row.iloc[0]
        merch_bank = str(merchant.get("bank"))
        merch_bents = bents_by_bank.get(merch_bank, [])
        if merch_bents:
            bent_rec = random.choice(merch_bents)
            bent_id = bent_rec.get("name")
            bent_loc = bent_rec.get("address")
        else:
            bent_id = generate_uuid(8)
            bent_loc = fake.address().replace("\n", ", ")

        tgt_acct = ProfileAccount(
            id=acct_id,
            owner_id=merchant["entity_id"],
            owner_type="Merchant",
            owner_name=merchant.get("name", ""),
            bank_name="",
        )

        ts_dt = generate_transaction_timestamp(start_dt, end_dt, entity_type="Company")
        timestamp = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
        post_date = generate_post_date(ts_dt).strftime("%Y-%m-%d %H:%M:%S")
        txn_id = generate_uuid()

        entries = split_transaction(
            txn_id=txn_id,
            timestamp=timestamp,
            src=None,
            tgt=tgt_acct,
            amount=round(amt, 2),
            currency="USD",
            payment_type="cash",
            is_laundering=False,
            known_accounts=known_accounts,
            post_date=post_date,
            atm_id=bent_id,
            atm_location=bent_loc
        )
        transactions.extend(entries)

    return transactions
