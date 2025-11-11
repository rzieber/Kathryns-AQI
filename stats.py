import warnings
import pandas as pd
import numpy as np
from pathlib import Path
import sensortoolkit as stk
from sensortoolkit import *
import argparse

def main(data:str, output:str):
    try:
        data = Path(data)
        output = Path(output)
    except Exception as e:
        print(f"Error parsing directory to Path: {e}")

    names = ['Payne Obs. Site', 'AJAX Reference', 'AQI Testbed', 'AJAX Co-Located']

    variable_mapper = { # 3D-PAWS : AJAX co-located site
        'pm1s10':'PM 1.0',
        'pm1s25':'PM 2.5',
        'pm1e10':'PM 1.0',
        'pm1e25':'PM 2.5'
    }

    """
    ========================================================================
    Dataframe creation.
    ========================================================================
    """
    dataframes = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)

        for csv in data.rglob("*.csv"):
            print(str(csv.name))
            df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])
            df['week'] = df['time'].dt.to_period('W')
            df.set_index('time')
            dataframes.append(df)

    print()

    # create statistical summary of the data
    # stats we care about: corr. coeff., rmse, std, 


def parse_args():
    parser = argparse.ArgumentParser(description="Calculates statistical properties from data.")

    parser.add_argument("data", type=str, help="The directory path where data is located.")
    parser.add_argument("output", type=str, help="The directory path where csv's are to be saved.")

    args = parser.parse_args()

    return args.data, args.output


if __name__ == '__main__':
    main(*parse_args())
