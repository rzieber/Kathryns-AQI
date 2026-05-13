import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import warnings


def main(data_path:str, output_path:str, aqi_threshold:float):
    """
    Reads all CSV files under data_path, normalizes them to a common format,
    and writes cleaned CSVs to output_path/cleaned/.

    Each data source (AJAX, CU Boulder, ECC, 3D-PAWS) has a different column
    structure and timezone convention, so each gets its own parsing block below.

    aqi_threshold: PM 2.5 values above this (µg/m³) are considered outliers.

    CONFIG:
      FILTER_OUTLIERS — replace outlier readings with NaN during cleaning and
                        write a separate outlier CSV. When False, outliers are
                        left in the data and flagged visually in plotter.py instead.
    """
    # ============================================================
    # CONFIG
    # ============================================================
    FILTER_OUTLIERS = False
    if not isinstance(aqi_threshold, float):
        raise TypeError(f"[ERROR]: cleaner.py requires aqi_threshold to be of type <float>, passed: {type(aqi_threshold)}")
    try:
        data = Path(data_path)
        output = Path(output_path)
    except Exception as e:
        print(f"Trouble parsing input string as directory: {e}")

    # ECC data arrives as multiple quarterly CSV files. We collect them here
    # and concatenate into a single file at the end.
    ecc_dfs = []

    for csv in data.rglob("*.csv"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)

            name = str(csv.stem)
            outliers = pd.DataFrame()
            df = None

            print("Reading", name)

            if name.startswith("UplandS"):
                """
                AJAX Reference Station (Upland Street, Erie CO)
                Minutely data, already in UTC. Drop columns not used in analysis.
                PM 10 is excluded — 3D-PAWS PM 10 is unreliable, so we drop it
                from the reference too for consistency.
                """
                df = pd.read_csv(csv, low_memory=False, parse_dates=['UTC Date Time'])
                df.rename(columns={'UTC Date Time':'time'}, inplace=True)
                df.drop(columns=['Local Date Time', 'PM 10', 'Wind Speed', 'Wind Direction',
                                 'Latitude', 'Longitude'], inplace=True)

                
            elif name.startswith("daily_"):
                """
                EPA daily aggregate files — not used in this study, skip them.
                """
                continue

            
            elif name.startswith("Marine Street"):
                """
                CU Boulder Reference Station (Marine Street, Boulder CO)
                Data is in local Denver time (MDT/MST). We convert to UTC.
                The DST transition on Nov 2 2025 01:00–02:00 MDT creates duplicate
                timestamps (clocks fall back); we drop that duplicated hour before
                localizing so pandas doesn't raise an ambiguous-time error.
                """
                df = pd.read_csv(csv, low_memory=False, parse_dates=['Date'])
                dst_mask = (df['Date'] >= "2025-11-02 01:00:00") & (df['Date'] < "2025-11-02 02:00:00")
                df = df[~dst_mask]
                df['Date'] = df['Date'].dt.tz_localize("America/Denver", ambiguous='infer')
                df['Date UTC'] = df['Date'].dt.tz_convert("UTC")
                df.rename(columns={'Date UTC':'time', 'PMFine':'PM 2.5'}, inplace=True)
                df.drop(columns=['PM10stp'], inplace=True)

            
            elif name.startswith("ECC"):
                """
                Erie Community Center Reference Station (ECC)
                Data comes in quarterly files with timestamps that include Excel
                formula artifacts (leading `=` and surrounding `"`). These are
                stripped before parsing. All quarterly files are combined into one
                output CSV at the end of this function.
                """
                df = pd.read_csv(csv, low_memory=False)
                df['Time UTC'] = df['Time UTC'].str.replace('=', '', regex=False)
                df['Time UTC'] = df['Time UTC'].str.replace('"', '', regex=False)
                df['Time UTC'] = pd.to_datetime(df['Time UTC'], format="%Y-%m-%d %H:%M")
                df.rename(columns={'Time UTC':'time'}, inplace=True)
                df.drop(columns=['PM 10'], inplace=True)
                ecc_dfs.append((df, outliers))
                # ECC files are not written individually — fall through to the
                # skip at the bottom so they're handled in the ECC-only block.

        
            else:
                """
                3D-PAWS Instruments (16, 18, 127, 153, 154)
                Timestamps are already UTC. Column 'pm1e25' is their internal name
                for PM 2.5; rename it so all sources share the same column name.
                """
                df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])
                df.rename(columns={'pm1e25':'PM 2.5'}, inplace=True)

            if FILTER_OUTLIERS:
                df['PM 2.5'] = pd.to_numeric(df['PM 2.5'], errors='coerce')
                mask = df['PM 2.5'] > aqi_threshold
                if mask.any():
                    outliers = pd.concat([outliers, df.loc[mask, ['time', 'PM 2.5']]], axis=0)
                df.loc[df['PM 2.5'] > aqi_threshold, 'PM 2.5'] = np.nan

            # ECC and daily files are skipped here — ECC is handled below.
            if name.startswith("daily_") or name.startswith("ECC"):
                continue

            (output / "cleaned").mkdir(parents=True, exist_ok=True)
            df.to_csv(output / "cleaned" / f"{name}_cleaned.csv", index=False)

            if not outliers.empty:
                (output / "outliers").mkdir(parents=True, exist_ok=True)
                outliers.to_csv(output / "outliers" / f"{name}_outliers.csv", index=False)

    # ECC: combine all quarterly files into one sorted CSV.
    if ecc_dfs:
        print("Reading ECC dfs ------")
        for i, (ecc_df, ecc_out) in enumerate(ecc_dfs):
            if not ecc_out.empty:
                # Strip timezone info so ECC timestamps are timezone-naive,
                # matching the other cleaned files.
                ecc_out['time'] = pd.to_datetime(ecc_out['time'], utc=True, errors='coerce')
                ecc_out['time'] = ecc_out['time'].dt.tz_localize(None)
            ecc_dfs[i] = (ecc_df, ecc_out)

        combined_df = pd.concat([e[0] for e in ecc_dfs], ignore_index=True)
        sorted_df = combined_df.sort_values('time').reset_index(drop=True)

        (output / "cleaned").mkdir(parents=True, exist_ok=True)
        sorted_df.to_csv(output / "cleaned" / "ECC_pm_complete_cleaned.csv", index=False)

        if FILTER_OUTLIERS:
            outliers_combined = pd.concat([e[1] for e in ecc_dfs if not e[1].empty], ignore_index=True)
            if not outliers_combined.empty:
                outliers_sorted = outliers_combined.sort_values('time').reset_index(drop=True)
                (output / "outliers").mkdir(parents=True, exist_ok=True)
                outliers_sorted.to_csv(output / "outliers" / "ECC_pm_complete_outliers.csv", index=False)


def parse_args():
    parser = argparse.ArgumentParser(description="2025 AQI sensor comparison study.")

    parser.add_argument("data_path",        type=str,   help="Directory path where data is located.")
    parser.add_argument("output_path",      type=str,   help="Directory path where cleaned data should be outputted.")
    parser.add_argument("aqi_threshold",    type=float, help="Flag values above this concentration (µg/m³) as outliers.")

    args = parser.parse_args()

    return args.data, args.output, args.aqi_threshold


if __name__ == '__main__':
    main(*parse_args())
