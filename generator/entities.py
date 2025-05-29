import random
import uuid
from faker import Faker
import pandas as pd

faker = Faker()

# === Constants ===
CURRENCIES = ["USD"]
BANK_NAMES = ["Chase", "Bank of America", "Wells Fargo", "Citi", "Capital One"]
VISIBILITY_OPTIONS = ["sender", "receiver", "both"]

# === Entity Types ===
class Bank:
    def __init__(self, name, id=None, code=None):
        self.id = id or str(uuid.uuid4())[:8]
        self.name = name
        self.code = str(code) if code is not None else str(random.randint(100, 999))

class Account:
    def __init__(self, owner_id, owner_type, bank_id, currency="USD", bank_code="000",
                 owner_name=None, bank_name=None, account_id=None):
        serial = random.randint(10**8, 10**9 - 1)
        self.id = account_id or f"{bank_code}{serial}"
        self.owner_id = owner_id
        self.owner_type = owner_type
        self.bank_id = bank_id
        self.currency = currency
        self.account_number = self.id
        # Optional context for downstream transaction rows
        self.owner_name = owner_name
        self.bank_name = bank_name

# === Base Entity ===
class Entity:
    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.accounts = []
        self.address = faker.address()
        self.phone = faker.phone_number()
        self.bank = None  # Assigned via account generation
        self.launderer = random.choice([True, False])
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

    def get_allowed_transactions(self):
        return {
            "ACH": ["Payroll", "Expense Reimbursement", "Loan", "Rent/Lease"],
            "Wire": ["Vendor/Supplier"],
            "Credit Card": ["Vendor/Supplier"],
            "Cash": ["Deposit", "Withdrawal"]
        }

# === Company Entity ===
class Company(Entity):
    def __init__(self):
        super().__init__()
        self.name = faker.company()

    def get_allowed_transactions(self):
        return {
            "ACH": ["Payroll", "Vendor/Supplier", "Expense Reimbursement", "Intercompany", "Loan", "Rent/Lease"],
            "Wire": ["Vendor/Supplier", "Intercompany", "Rent/Lease"],
            "Check": ["Expense Reimbursement", "Vendor/Supplier", "Miscellaneous"],
            "Credit Card": ["Vendor/Supplier"],
            "Cash": ["Deposit", "Withdrawal"]
        }

# === Generators ===
def create_banks(n=3):
    names = random.sample(BANK_NAMES, min(n, len(BANK_NAMES)))
    return [Bank(name=name) for name in names]

def create_individuals(n=10):
    return [Person() for _ in range(n)]

def create_companies(n=5):
    return [Company() for _ in range(n)]

def assign_accounts(entities, banks, accounts_per_entity=(1, 3)):
    all_accounts = []
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
                bank_name=bank.name
            )
            entity.accounts.append(account)
            all_accounts.append(account)
    return all_accounts


def load_entities_from_excel(path, sheet="Combined_Data"):
    """Load entity and account definitions from an Excel sheet."""
    df = pd.read_excel(path, sheet_name=sheet)
    df.columns = [c.strip().lower() for c in df.columns]

    banks = []
    individuals = []
    companies = []
    all_entities = []
    accounts = []

    bank_map = {}

    # Create banks first so accounts can reference them
    bank_rows = df[df.get("type") == "bank"]
    for _, row in bank_rows.iterrows():
        bank_code = str(row.get("bank")) if not pd.isna(row.get("bank")) else None
        bank = Bank(name=row.get("name", "Bank"), id=str(row.get("entity_id")), code=bank_code)
        if not pd.isna(row.get("address")):
            bank.address = row.get("address")
        banks.append(bank)
        all_entities.append(bank)
        if bank_code:
            bank_map[str(bank_code)] = bank
        bank_map[bank.id] = bank

    def find_bank(value):
        if pd.isna(value):
            return None
        key = str(int(value)) if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)
        return bank_map.get(key)

    for _, row in df[df.get("type") != "bank"].iterrows():
        typ = row.get("type", "company")
        if typ == "person":
            entity = Person()
            individuals.append(entity)
        else:
            entity = Company()
            companies.append(entity)
        entity.id = str(row.get("entity_id"))
        if not pd.isna(row.get("name")):
            entity.name = row.get("name")
        if not pd.isna(row.get("address")):
            entity.address = row.get("address")
        if not pd.isna(row.get("phone_number")):
            entity.phone = row.get("phone_number")

        all_entities.append(entity)

        bank = find_bank(row.get("bank"))
        acct_no = row.get("account_number")
        if bank and not pd.isna(acct_no):
            acct_id = str(int(acct_no)) if isinstance(acct_no, (int, float)) else str(acct_no)
            account = Account(
                owner_id=entity.id,
                owner_type=entity.__class__.__name__,
                bank_id=bank.id,
                currency="USD",
                bank_code=bank.code,
                owner_name=entity.name,
                bank_name=bank.name,
                account_id=acct_id,
            )
            entity.accounts.append(account)
            accounts.append(account)

    return {
        "banks": banks,
        "individuals": individuals,
        "companies": companies,
        "entities": all_entities,
        "accounts": accounts,
    }

# === Top-level function ===
def generate_entities(n_banks=3, n_individuals=10, n_companies=5, entity_file=None):
    if entity_file:
        return load_entities_from_excel(entity_file)

    banks = create_banks(n_banks)
    individuals = create_individuals(n_individuals)
    companies = create_companies(n_companies)
    all_entities = individuals + companies
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
