import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import warnings

def main(data:str, output:str, aqi_threshold:float):
    try:
        data = Path(data)
        output = Path(output)
    except Exception as e:
        print(f"Trouble parsing input string as directory: {e}")

    variable_mapper = { # 3D-PAWS : AJAX co-located site
        'pm1s10':'PM 1.0',
        'pm1s25':'PM 2.5',
        'pm1e10':'PM 1.0',
        'pm1e25':'PM 2.5'
    }


    outliers = pd.DataFrame()

    for csv in data.rglob("*.csv"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            """
            ========================================================================
            Dataframe creation.
            ========================================================================
            """
            name = str(csv.stem)
            df = None

            print("Reading", name)

            is_ajax = False
            if name.startswith("UplandS"):
                df = pd.read_csv(csv, low_memory=False, parse_dates=['UTC Date Time'])
                df.rename(columns={'UTC Date Time':'time'}, inplace=True)
                is_ajax = True

            elif name.startswith("daily_"): continue

            else: 
                df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])

        """
        ========================================================================
        Filter out AQI's above set threshold aqi_threshold.
        ========================================================================
        """
        for var_3dpaws, var_ajax in variable_mapper.items():
            col = var_ajax if is_ajax else var_3dpaws

            if col not in df.columns:          
                continue

            df[col] = pd.to_numeric(df[col], errors='coerce')

            mask = df[col] > aqi_threshold     
            if mask.any():
                outliers = pd.concat([outliers, df.loc[mask, ['time', col]]], axis=0)

            df.loc[df[col] > aqi_threshold, col] = np.nan

        (output / "cleaned").mkdir(parents=True, exist_ok=True)
        df.to_csv(output / "cleaned" / f"{name}_cleaned.csv", index=False)  

        if not outliers.empty: 
            (output / "outliers").mkdir(parents=True, exist_ok=True)
            outliers.to_csv(output / "outliers" / f"{name}_outliers.csv", index=False) 


def parse_args():
    parser = argparse.ArgumentParser(description="2025 AQI sensor comparison study.")

    parser.add_argument("data", type=str, help="Directory path where data is located.")
    parser.add_argument("output", type=str, help="Directory path where cleaned data should be outputted.")
    parser.add_argument("aqi_threshold", type=float, help="Filter out any values above the threshold concentration (µg/m³).")

    args = parser.parse_args()

    return args.data, args.output, args.aqi_threshold


if __name__ == '__main__':
    main(*parse_args())