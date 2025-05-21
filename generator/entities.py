import random
import uuid
from faker import Faker

fake = Faker()

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

class Person:
    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.name = fake.name()
        self.accounts = []

class Company:
    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.name = fake.company()
        self.accounts = []

# === Generators ===
def create_banks(n=3):
    return [Bank(name=fake.company() + " Bank") for _ in range(n)]

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
                #currency=random.choice(["USD", "EUR", "CHF"])
                currency="USD"  # Default to USD for simplicity
            )
            entity.accounts.append(account)
            all_accounts.append(account)
    return all_accounts

# === Top-level function for ease of use ===
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
        "accounts": accounts
    }
