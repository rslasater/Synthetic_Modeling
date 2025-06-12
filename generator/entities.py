import random
import uuid
import os
import pandas as pd
from faker import Faker
from utils.helpers import generate_card_number

faker = Faker()

# === Constants ===
CURRENCIES = ["USD"]
BANK_NAMES = ["Chase", "Bank of America", "Wells Fargo", "Citi", "Capital One"]
VISIBILITY_OPTIONS = ["sender", "receiver", "both"]

# === Entity Types ===
class Bank:
    def __init__(self, name, code=None, swift_code="", aba_routing_number=""):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.code = str(code) if code is not None else str(random.randint(100, 999))
        # Wire metadata comes from profile data if available
        self.swift_code = swift_code
        self.aba_routing_number = aba_routing_number

class Account:
    def __init__(
        self,
        owner_id,
        owner_type,
        bank_id,
        currency="USD",
        bank_code="000",
        account_number=None,
        owner_name=None,
        bank_name=None,
        country="United States",
        swift_code=None,
        routing_number=None,
        credit_card_number=None,
        debit_card_number=None,
        receiving_method=None,
        launderer=False,
    ):
        if account_number is not None:
            self.id = str(account_number)
        else:
            serial = random.randint(10**8, 10**9 - 1)
            self.id = f"{bank_code}{serial}"
        self.owner_id = owner_id
        self.owner_type = owner_type
        self.bank_id = bank_id
        self.bank_code = bank_code
        # Alias for backward compatibility
        self.bank = bank_code
        self.currency = currency
        self.account_number = self.id
        # Optional context for downstream transaction rows
        self.owner_name = owner_name
        self.bank_name = bank_name
        self.country = country
        self.swift_code = swift_code
        self.routing_number = routing_number
        self.credit_card_number = credit_card_number
        self.debit_card_number = debit_card_number
        self.receiving_method = receiving_method
        self.launderer = launderer

# === Base Entity ===
class Entity:
    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.accounts = []
        self.address = faker.address()
        self.phone = faker.phone_number()
        self.bank = None  # Assigned via account generation
        # Majority of entities are US based
        self.country = "United States" if random.random() < 0.8 else faker.country()
        # Accounts will be flagged as laundering participants after
        # laundering transactions are generated
        self.launderer = False
        self.visibility = random.choices(
            VISIBILITY_OPTIONS,
            weights=[0.25, 0.25, 0.5]  # Bias toward 'both'
        )[0]

    def get_allowed_transactions(self):
        raise NotImplementedError("Override this in subclass.")

# === Person Entity ===
class Person(Entity):
    def __init__(self):
        super().__init__()
        self.name = faker.name()
        self.credit_card_number = generate_card_number()
        self.debit_card_number = generate_card_number()

    def get_allowed_transactions(self):
        return {
            "ACH": ["Payroll", "Expense Reimbursement", "Loan", "Rent/Lease"],
            "Wire": ["Vendor/Supplier"],
            "POS": ["Vendor/Supplier"],
            "Cash": ["Deposit", "Withdrawal"]
        }

# === Company Entity ===
class Company(Entity):
    def __init__(self):
        super().__init__()
        self.name = faker.company()
        self.credit_card_number = generate_card_number()
        self.debit_card_number = generate_card_number()
        self.receiving_method = random.choice([
            "CARD PAYMENT",
            "ONLINE PAYMENT",
            "PHONE PAYMENT AUTHORIZED",
        ])

    def get_allowed_transactions(self):
        return {
            "ACH": ["Payroll", "Vendor/Supplier", "Expense Reimbursement", "Intercompany", "Loan", "Rent/Lease"],
            "Wire": ["Vendor/Supplier", "Intercompany", "Rent/Lease"],
            "Check": ["Expense Reimbursement", "Vendor/Supplier", "Miscellaneous"],
            "POS": ["Vendor/Supplier"],
            "Cash": ["Deposit", "Withdrawal"]
        }

# === Generators ===
def create_banks(n=3, profiles_path=None):
    """Create ``Bank`` objects.

    If ``profiles_path`` is provided and points to an Excel file with a
    ``banks`` sheet, use that metadata (including SWIFT and routing numbers).
    Otherwise fall back to simple placeholder banks without wire details.
    """
    if profiles_path and os.path.exists(profiles_path):
        try:
            banks_df = pd.read_excel(profiles_path, sheet_name="banks")
            if not banks_df.empty:
                sample_df = banks_df.sample(min(n, len(banks_df)))
                return [
                    Bank(
                        name=row.get("name", ""),
                        code=row.get("bank"),
                        swift_code=row.get("swift_code", ""),
                        aba_routing_number=str(row.get("aba_routing_number", "")),
                    )
                    for _, row in sample_df.iterrows()
                ]
        except Exception:
            pass

    names = random.sample(BANK_NAMES, min(n, len(BANK_NAMES)))
    return [Bank(name=name) for name in names]

def create_individuals(n=10, profiles_df=None):
    """Return a list of ``Person`` objects.

    When ``profiles_df`` is provided it should contain the columns
    ``entity_id`` and ``name`` at minimum. The dataframe will be sampled
    to the requested ``n`` and the data used to populate the objects.
    """
    if profiles_df is not None and not profiles_df.empty:
        sample_df = profiles_df.sample(min(n, len(profiles_df)))
        people = []
        for _, row in sample_df.iterrows():
            p = Person()
            p.id = str(row.get("entity_id", p.id))
            p.name = row.get("name", p.name)
            p.address = row.get("address", p.address)
            p.phone = row.get("phone_number", p.phone)
            people.append(p)
        if len(people) < n:
            people.extend(Person() for _ in range(n - len(people)))
        return people
    return [Person() for _ in range(n)]

def create_companies(n=5, profiles_df=None):
    """Return a list of ``Company`` objects."""
    if profiles_df is not None and not profiles_df.empty:
        sample_df = profiles_df.sample(min(n, len(profiles_df)))
        comps = []
        for _, row in sample_df.iterrows():
            c = Company()
            c.id = str(row.get("entity_id", c.id))
            c.name = row.get("name", c.name)
            c.address = row.get("address", c.address)
            c.phone = row.get("phone_number", c.phone)
            comps.append(c)
        if len(comps) < n:
            comps.extend(Company() for _ in range(n - len(comps)))
        return comps
    return [Company() for _ in range(n)]

def assign_accounts(entities, banks, accounts_per_entity=(1, 3), profiles_df=None):
    all_accounts = []
    bank_lookup = {str(b.code): b for b in banks}

    if profiles_df is not None and not profiles_df.empty:
        for entity in entities:
            rows = profiles_df[profiles_df["entity_id"] == entity.id]
            if rows.empty:
                continue
            row = rows.iloc[0]
            bank_code = str(row.get("bank")) if not pd.isna(row.get("bank")) else random.choice(list(bank_lookup.keys()))
            bank = bank_lookup.get(bank_code, random.choice(banks))
            acct_num = row.get("account_number")
            if pd.isna(acct_num):
                acct_num = faker.unique.random_number(digits=9, fix_len=True)
            account = Account(
                owner_id=entity.id,
                owner_type=entity.__class__.__name__,
                bank_id=bank.id,
                currency=random.choice(CURRENCIES),
                bank_code=bank.code,
                account_number=acct_num,
                owner_name=entity.name,
                bank_name=bank.name,
                country=entity.country,
                swift_code=bank.swift_code or faker.swift8(),
                routing_number=bank.aba_routing_number or faker.aba(),
                credit_card_number=getattr(entity, "credit_card_number", None),
                debit_card_number=getattr(entity, "debit_card_number", None),
                receiving_method=getattr(entity, "receiving_method", None),
                launderer=entity.launderer,
            )
            entity.accounts.append(account)
            all_accounts.append(account)
        return all_accounts

    for entity in entities:
        num_accounts = random.randint(*accounts_per_entity)
        for _ in range(num_accounts):
            bank = random.choice(banks)
            account = Account(
                owner_id=entity.id,
                owner_type=entity.__class__.__name__,
                bank_id=bank.id,
                currency=random.choice(CURRENCIES),
                bank_code=bank.code,
                owner_name=entity.name,
                bank_name=bank.name,
                country=entity.country,
                swift_code=bank.swift_code,
                routing_number=bank.aba_routing_number,
                credit_card_number=getattr(entity, "credit_card_number", None),
                debit_card_number=getattr(entity, "debit_card_number", None),
                receiving_method=getattr(entity, "receiving_method", None),
                launderer=entity.launderer,
            )
            entity.accounts.append(account)
            all_accounts.append(account)
    return all_accounts

# === Top-level function ===
def generate_entities(
    n_banks: int = 3,
    n_individuals: int = 10,
    n_companies: int = 5,
    profile_path: str | None = None,
):
    """Generate banks, individuals and companies.

    When ``profile_path`` is supplied the Excel file will be used to
    populate the agent names and metadata. Regardless of the source,
    persons and companies are randomly flagged as laundering agents so
    that some accounts will later participate in laundering flows.
    """

    if profile_path and os.path.exists(profile_path):
        try:
            banks_df_full = pd.read_excel(profile_path, sheet_name="banks")
            n_banks = max(n_banks, len(banks_df_full))
        except Exception:
            banks_df_full = None
    else:
        banks_df_full = None

    banks = create_banks(n_banks, profiles_path=profile_path)

    people_df = None
    company_df = None
    if profile_path and os.path.exists(profile_path):
        try:
            people_df = pd.read_excel(profile_path, sheet_name="People")
        except Exception:
            people_df = None
        try:
            company_df = pd.read_excel(profile_path, sheet_name="Companies1")
        except Exception:
            company_df = None

    sample_people_df = people_df
    sample_company_df = company_df
    if people_df is not None and not people_df.empty:
        sample_people_df = people_df.sample(min(n_individuals, len(people_df)))
        individuals = []
        for _, row in sample_people_df.iterrows():
            p = Person()
            p.id = str(row.get("entity_id", p.id))
            p.name = row.get("name") if pd.notna(row.get("name")) else faker.name()
            p.address = row.get("address") if pd.notna(row.get("address")) else faker.address()
            p.phone = row.get("phone_number") if pd.notna(row.get("phone_number")) else faker.phone_number()
            individuals.append(p)
        if len(individuals) < n_individuals:
            individuals.extend(Person() for _ in range(n_individuals - len(individuals)))
    else:
        individuals = create_individuals(n_individuals)
        sample_people_df = None

    if company_df is not None and not company_df.empty:
        sample_company_df = company_df.sample(min(n_companies, len(company_df)))
        companies = []
        for _, row in sample_company_df.iterrows():
            c = Company()
            c.id = str(row.get("entity_id", c.id))
            c.name = row.get("name") if pd.notna(row.get("name")) else faker.company()
            c.address = row.get("address") if pd.notna(row.get("address")) else faker.address()
            c.phone = row.get("phone_number") if pd.notna(row.get("phone_number")) else faker.phone_number()
            companies.append(c)
        if len(companies) < n_companies:
            companies.extend(Company() for _ in range(n_companies - len(companies)))
    else:
        companies = create_companies(n_companies)
        sample_company_df = None

    all_entities = individuals + companies
    # Randomly flag entities as laundering participants
    for ent in all_entities:
        ent.launderer = random.choice([True, False])

    if profile_path and (sample_people_df is not None or sample_company_df is not None):
        account_df_list = []
        if sample_people_df is not None:
            account_df_list.append(sample_people_df[["entity_id", "bank", "account_number"]])
        if sample_company_df is not None:
            account_df_list.append(sample_company_df[["entity_id", "bank", "account_number"]])
        profiles_df = pd.concat(account_df_list, ignore_index=True) if account_df_list else None
        accounts = assign_accounts(all_entities, banks, profiles_df=profiles_df)
    else:
        accounts = assign_accounts(all_entities, banks)
    return {
        "banks": banks,
        "individuals": individuals,
        "companies": companies,
        "entities": all_entities,
        "accounts": accounts,
    }

def get_known_accounts(accounts, n_known=100):
    return random.sample(accounts, min(n_known, len(accounts)))
