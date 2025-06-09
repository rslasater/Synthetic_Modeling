import streamlit as st
import subprocess
import os

st.title("Synthetic AML Dataset Generator")

# === CLI arguments ===
individuals = st.number_input("Number of individuals", min_value=1, value=10)
companies = st.number_input("Number of companies", min_value=0, value=5)
banks = st.number_input("Number of banks", min_value=1, value=3)
legit_txns = st.number_input("Number of legitimate transactions", min_value=0, value=500)
laundering_chains = st.number_input("Number of laundering chains", min_value=0, value=10)
patterns = st.text_input("Path to laundering patterns YAML file", value="")
agent_profiles = st.text_input("Path to agent profiles Excel file", value="")
output = st.text_input("Output file path", value="data/aml_dataset.xlsx")
export_format = st.selectbox("Export format", options=["csv", "xlsx"], index=1)
known_account_ratio = st.slider("Known account ratio", min_value=0.0, max_value=1.0, value=0.5)
start_date = st.date_input("Start date", value=None, key="start")
end_date = st.date_input("End date", value=None, key="end")

start_str = start_date.isoformat() if start_date else "2025-01-01"
end_str = end_date.isoformat() if end_date else "2025-01-31"

if st.button("Generate"):
    cmd = [
        "python", "main.py",
        "--individuals", str(individuals),
        "--companies", str(companies),
        "--banks", str(banks),
        "--legit_txns", str(legit_txns),
        "--laundering_chains", str(laundering_chains),
        "--output", output,
        "--format", export_format,
        "--known_account_ratio", str(known_account_ratio),
        "--start_date", start_str,
        "--end_date", end_str,
    ]
    if patterns:
        cmd += ["--patterns", patterns]
    if agent_profiles:
        cmd += ["--agent_profiles", agent_profiles]

    with st.spinner("Generating dataset..."):
        result = subprocess.run(cmd, capture_output=True, text=True)
        st.text(result.stdout)
        if result.stderr:
            st.error(result.stderr)
