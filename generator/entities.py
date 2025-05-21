import random
import uuid
from faker import Faker

faker = Faker()

# === Constants ===
CURRENCIES = ["USD"]
BANK_NAMES = ["Chase", "Bank of America", "Wells Fargo", "Citi", "Capital One"]
VISIBILITY_OPTIONS = ["sender", "receiver", "both"]

# === Entity Types ===
class Bank:
    def __init__(self, name):
        self.id = str(uuid.uuid4())[:8]
        self.name = name

class Account:
    def __init__(self, owner_id, owner_type, bank_id, currency="USD"):
        self.id = str(uuid.uuid4())[:12]
        self.owner_id = owner_id
        self.owner_type = owner_type
        self.bank_id = bank_id
        self.currency = currency
        self.account_number = str(random.randint(10**9, 10**10 - 1))

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
                currency=random.choice(CURRENCIES)
            )
            entity.accounts.append(account)
            all_accounts.append(account)
    return all_accounts

# === Top-level function ===
def generate_entities(n_banks=3, n_individuals=10, n_companies=5):
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
        "accounts": accounts
    }

def get_known_accounts(accounts, n_known=100):
    return random.sample(accounts, min(n_known, len(accounts)))
