#!/usr/bin/env python3

import pandas as pd
import argparse

def fetch_table() -> pd.DataFrame:
    """Download MCC/MNC allocations from mcc-mnc.com"""
    all_tables = pd.read_html("https://www.mcc-mnc.com", attrs = {'id': 'mncmccTable'}, converters={"MCC": str, "MNC": str})
    operator_table = all_tables[0]
    operator_table = operator_table.fillna("000")

    # zero-pad MNC and MCC
    operator_table["MCC"] = operator_table["MCC"].apply(lambda x: x.rjust(3, '0'))
    operator_table["MNC"] = operator_table["MNC"].apply(lambda x: x.rjust(3, '0'))
    return operator_table

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output_file', type = str, help = 'Output file')
    args = parser.parse_args()
    
    print("Fetching MCC-MNC table…")
    operators = fetch_table()

    print(f"Got {len(operators)} entries. Preview:")
    print(operators.head())
    print("…")

    print(f"Writing to CSV: {args.output_file}")
    operators[["MCC", "MNC", "Network"]].to_csv(args.output_file, index=False)