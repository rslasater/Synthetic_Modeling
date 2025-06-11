# Synthetic AML Dataset Generator

This project generates small-scale, realistic anti-money laundering (AML) datasets using synthetic transaction patterns. Designed for educational use, the output is suitable for Excel-based analysis and classroom exercises.

---

## Features

- Generate financial transactions with realistic timestamps, payment types, and currencies.
- Simulate common laundering patterns such as fan-out, cycles, and scatter-gather.
- Label laundering transactions for easy classification.
- Export clean `.csv` or `.xlsx` files for Excel.
- Cash transactions now include a `channel` field (`ATM` or `Teller`). Amounts
  handled at an ATM are rounded to the nearest $20 and limited to $500. When a
  transaction is selected as cash, the base amount is divided by a random value
  between 2 and 5 to reflect everyday spending. If the result still exceeds $500,
  the generator creates multiple ATM withdrawals (5% chance) or a single teller
  transaction (95% chance), unless overridden by a laundering pattern.
- Descriptions for merchant purchases now leverage an NLP-based model to
  infer the transaction type from NAICS codes and whether the payer is a person
  or company. Each NAICS category includes multiple description options and the
  generator randomly selects one to add variety.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-org/aml-synthetic-generator.git
cd aml-synthetic-generator
```

### 2. Create a Virtual Environment

Make sure that you have Python 3.10 installed.

```bash
python3 -m venv aml-env
source aml-env/bin/activate 
```
### 3. Install Dependencies

```bash
pip3 install -r requirements.txt
```

# Files
### Patterns.yaml
The patterns.yaml file contains the instructions for each money laundering technique.

| Field                     | Description                                                                                         |
| ------------------------- | --------------------------------------------------------------------------------------------------- |
| `type`                    | Type of laundering pattern (`cycle`, `fan_out`, `fan_in`, `scatter_gather`, `gather_scatter`, `cash_structuring`, etc.) |
| `instances`               | How many times to inject this pattern                                                               |
| `amount` / `total_amount` | Total amount to launder or per transaction                                                          |
| `accounts_per_*`          | How many accounts are involved (varies by pattern)                                                  |
| `currency`                | Optional override from default                                                                      |
| `start_date`, `end_date`  | Timestamp range to assign to transactions                                                           |
| `label`                   | Whether transactions should be marked as laundering                                                 |

Example `cash_structuring` pattern:

```yaml
  - type: cash_structuring
    instances: 1
    accounts: 2
    transactions_per_account: 5
    max_deposit: 10000
    atm_ratio: 0.6
    start_date: "2025-01-21"
    end_date: "2025-01-25"
    label: true
```

### Agent Profiles
If you have a structured Excel file of agent profiles, you can generate transactions based on that data:

```bash
python main.py --agent_profiles agents/agent_profiles.xlsx
```

The generator will read merchant patterns, frequencies, payment methods, and average expenses to create realistic transactions between the entities defined in the file.

### BEnt Entities (ATMs/Tellers)
`BEnt` rows in the agent profiles represent bank entities such as ATMs or teller locations. They provide the IDs and addresses used when cash withdrawals and deposits occur. Be sure to include them in the profile data so cash transactions can reference the correct location. If no `BEnt` information is provided, the generator will create placeholder ATMs.
ATM withdrawals are limited to $500. When cash needs exceed this limit, the generator usually records a teller transaction but will occasionally split the amount into several ATM withdrawals. Laundering patterns may override these rules.

