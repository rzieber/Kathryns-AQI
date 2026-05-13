import warnings
import pandas as pd
import numpy as np
from pathlib import Path
import argparse

# sensortoolkit is EPA's analysis library for evaluating low-cost sensors against
# regulatory-grade reference instruments. It's not installed in this environment,
# so the import is commented out. If you have it installed, uncomment these lines
# and see https://sensortoolkit.readthedocs.io for usage.
# import sensortoolkit as stk
# from sensortoolkit import *


def main(data:str, output:str):
    """
    Reads cleaned and outlier CSVs from data/, counts outliers per station,
    and writes a summary CSV to output/.

    Currently implemented:
      - Total outlier count per station  →  total_outliers.csv

    Not yet implemented (see TODO comment at the bottom):
      - Correlation coefficient, RMSE, standard deviation per station pair
        (these are computed per-comparison in plotter.py but not aggregated here)
    """
    try:
        data = Path(data)
        output = Path(output)
    except Exception as e:
        print(f"Error parsing directory to Path: {e}")

    # variable_mapper translates between 3D-PAWS internal column names and
    # the standardized names used by the AJAX reference station.
    # Only PM 1.0 and PM 2.5 are used — PM 10 from 3D-PAWS is unreliable.
    variable_mapper = {
        'pm1s10': 'PM 1.0',   # 3D-PAWS standard PM 1.0
        'pm1s25': 'PM 2.5',   # 3D-PAWS standard PM 2.5
        'pm1e10': 'PM 1.0',   # 3D-PAWS extended PM 1.0
        'pm1e25': 'PM 2.5'    # 3D-PAWS extended PM 2.5 (renamed to 'PM 2.5' by cleaner.py)
    }

    # ============================================================
    # Load all cleaned and outlier CSVs
    # ============================================================
    dataframes = []
    outliers = {}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        warnings.simplefilter("ignore", category=FutureWarning)

        for csv in data.rglob("*.csv"):
            name = str(csv.stem)
            df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])

            print("Reading", name)

            df['week'] = df['time'].dt.to_period('W')
            df['day']  = df['time'].dt.to_period('D')
            df['hour'] = df['time'].dt.to_period('H')
            df.set_index('time')

            if name.endswith("_outliers"):
                # Outlier files are written by cleaner.py when outlier filtering is enabled.
                # Count how many rows (individual outlier readings) exist per station.
                outliers[name] = len(df)
            elif name.endswith("_cleaned"):
                dataframes.append(df)
            else:
                continue

    # Write outlier counts. If no outlier files were found (because filtering is
    # disabled in cleaner.py), this will produce an empty table — that's expected.
    pd.DataFrame(
        list(outliers.items()), columns=['Station Name', 'Number of Outliers']
    ).to_csv(output / "total_outliers.csv", index=False)

    print()

    # TODO: aggregate per-pair statistics (r, RMSE, std) across all station combinations.
    # These are currently computed inside plotter._stats_and_scatter() but only printed
    # to the console, not saved here. Consider pulling that logic into a shared helper
    # and calling it from both plotter.py and stats.py.


def parse_args():
    parser = argparse.ArgumentParser(description="Calculates statistical properties from data.")

    parser.add_argument("data",   type=str, help="The directory path where data is located.")
    parser.add_argument("output", type=str, help="The directory path where CSVs are to be saved.")

    args = parser.parse_args()

    return args.data, args.output


if __name__ == '__main__':
    main(*parse_args())
