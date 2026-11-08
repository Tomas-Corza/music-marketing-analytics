"""Inventory exported CSV files and check basic structural integrity."""
import argparse
from pathlib import Path
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', default='data')
    args = parser.parse_args()
    directory = Path(args.directory)
    files = sorted(directory.rglob('*.csv'))
    if not files:
        parser.error(f'No CSVs found in {directory}')
    for path in files:
        try:
            data = pd.read_csv(path)
            print(f'{path}: {len(data)} rows, {len(data.columns)} columns')
        except Exception as exc:
            print(f'{path}: ERROR {exc}')


if __name__ == '__main__':
    main()
