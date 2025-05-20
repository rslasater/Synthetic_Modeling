# Synthetic AML Dataset Generator

This project generates small-scale, realistic anti-money laundering (AML) datasets using synthetic transaction patterns. Designed for educational use, the output is suitable for Excel-based analysis and classroom exercises.

---

## Features

- Generate financial transactions with realistic timestamps, payment types, and currencies.
- Simulate common laundering patterns such as fan-out, cycles, and scatter-gather.
- Label laundering transactions for easy classification.
- Export clean `.csv` or `.xlsx` files for Excel.

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
| `type`                    | Type of laundering pattern (`cycle`, `fan_out`, `fan_in`, `scatter_gather`, `gather_scatter`, etc.) |
| `instances`               | How many times to inject this pattern                                                               |
| `amount` / `total_amount` | Total amount to launder or per transaction                                                          |
| `accounts_per_*`          | How many accounts are involved (varies by pattern)                                                  |
| `currency`                | Optional override from default                                                                      |
| `start_date`, `end_date`  | Timestamp range to assign to transactions                                                           |
| `label`                   | Whether transactions should be marked as laundering                                                 |

