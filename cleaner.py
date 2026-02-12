import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import warnings
import sys

gap_filler_path = Path("/Users/rzieber/Documents/GitHub/3D-PAWS_Data_Processing_Tools/data_gap_filler.py")
sys.path.insert(0, str(gap_filler_path.parent))
import data_gap_filler # shows a warning but runs fine (don't ask me why i just work here)


def main(data_path:str, output_path:str, aqi_threshold:float):
    if not isinstance(aqi_threshold, float):
        raise TypeError(f"[ERROR]: cleaner.py requires aqi_threshold to be of type <float>, passed: {type(aqi_threshold)}")
    try:
        data = Path(data_path)
        output = Path(output_path)
    except Exception as e:
        print(f"Trouble parsing input string as directory: {e}")


    ecc_dfs = []
    for csv in data.rglob("*.csv"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            """
            ========================================================================
            Dataframe creation.
            ========================================================================
            """
            name = str(csv.stem)
            outliers = pd.DataFrame()
            df = None

            print("Reading", name)

            if name.startswith("UplandS"):          # AJAX reference station
                df = pd.read_csv(csv, low_memory=False, parse_dates=['UTC Date Time'])
                df.rename(columns={'UTC Date Time':'time'}, inplace=True)
                df.drop(columns=['Local Date Time', 'PM 10', 'Wind Speed', 'Wind Direction',
                                 'Latitude', 'Longitude'], inplace=True)

            elif name.startswith("daily_"): continue

            elif name.startswith("Marine Street"):  # CU Boulder reference station
                df = pd.read_csv(csv, low_memory=False, parse_dates=['Date'])
                dst_mask = (df['Date'] >= "2025-11-02 01:00:00") & (df['Date'] < "2025-11-02 02:00:00")
                df = df[~dst_mask] # remove duplicate timestamps from MDT -> MST transition
                df['Date'] = df['Date'].dt.tz_localize("America/Denver", ambiguous='infer')
                df['Date UTC'] = df['Date'].dt.tz_convert("UTC")
                df.rename(columns={'Date UTC':'time', 'PMFine':'PM 2.5'}, inplace=True)
                df.drop(columns=['PM10stp'], inplace=True)

            elif name.startswith("ECC"):            # Erie Community Center reference station
                df = pd.read_csv(csv, low_memory=False)
                df['Time UTC'] = df['Time UTC'].str.replace('=', '', regex=False)
                df['Time UTC'] = df['Time UTC'].str.replace('"', '', regex=False)
                df['Time UTC'] = pd.to_datetime(df['Time UTC'], format="%Y-%m-%d %H:%M")
                df.rename(columns={'Time UTC':'time'}, inplace=True)
                df.drop(columns=['PM 10'], inplace=True)
                ecc_dfs.append((df, outliers))

            else:                                   # 3D-PAWS stations
                df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])
                df.rename(columns={'pm1e25':'PM 2.5'}, inplace=True)

            """
            ========================================================================
            Filter out AQI's above set threshold aqi_threshold.
            ========================================================================
            """
            # df['PM 2.5'] = pd.to_numeric(df['PM 2.5'], errors='coerce')
            # mask = df['PM 2.5'] > aqi_threshold     
            # if mask.any():
            #     outliers = pd.concat([outliers, df.loc[mask, ['time', 'PM 2.5']]], axis=0)
            # df.loc[df['PM 2.5'] > aqi_threshold, 'PM 2.5'] = np.nan
        
            """
            ========================================================================
            Generate csv's
            ========================================================================
            """
            if name.startswith("daily_") or name.startswith("ECC"): continue

            (output / "cleaned").mkdir(parents=True, exist_ok=True)
            df.to_csv(output / "cleaned" / f"{name}_cleaned.csv", index=False)

            if not outliers.empty: 
                (output / "outliers").mkdir(parents=True, exist_ok=True)
                outliers.to_csv(output / "outliers" / f"{name}_outliers.csv", index=False) 

    """
    ========================================================================
    Generate csv's (ECC only)
    ========================================================================
    """
    if ecc_dfs:
        print("Reading ECC dfs ------")
        for i, (ecc_df, ecc_out) in enumerate(ecc_dfs):
            if not ecc_out.empty:
                ecc_out['time'] = pd.to_datetime(ecc_out['time'], utc=True, errors='coerce')
                ecc_out['time'] = ecc_out['time'].dt.tz_localize(None)
            ecc_dfs[i] = (ecc_df, ecc_out)

        combined_df = pd.concat([e[0] for e in ecc_dfs], ignore_index=True)
        sorted_df = combined_df.sort_values('time').reset_index(drop=True)

        # outliers_combined = pd.concat([e[1] for e in ecc_dfs if not e[1].empty],
        #                             ignore_index=True)

        # if not outliers_combined.empty:
        #     outliers_sorted = outliers_combined.sort_values('time').reset_index(drop=True)

        (output / "cleaned").mkdir(parents=True, exist_ok=True)
        sorted_df.to_csv(output / "cleaned" / "ECC_pm_complete_cleaned.csv", index=False)

        # if not outliers_combined.empty:
        #     (output / "outliers").mkdir(parents=True, exist_ok=True)
        #     outliers_sorted.to_csv(output / "outliers" / "ECC_pm_complete_outliers.csv",
        #                         index=False)
        
def parse_args():
    parser = argparse.ArgumentParser(description="2025 AQI sensor comparison study.")

    parser.add_argument("data_path",        type=str,       help="Directory path where data is located.")
    parser.add_argument("output_path",      type=str,       help="Directory path where cleaned data should be outputted.")
    parser.add_argument("aqi_threshold",    type=float,     help="Filter out any values above the threshold concentration (µg/m³).")

    args = parser.parse_args()

    return args.data, args.output, args.aqi_threshold


if __name__ == '__main__':
    main(*parse_args())