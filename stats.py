import warnings
import pandas as pd
from pathlib import Path
import argparse
import analysis


def main(data:str, output:str):
    """
    Reads cleaned CSVs from data/, computes pairwise hourly-average statistics
    for all instrument combinations in the selected study, and writes summary CSVs
    to output/.

    Outputs:
      pair_stats.csv     — slope, intercept, r, RMSE, bias per instrument pair
      total_outliers.csv — outlier reading count per station (only populated when
                           FILTER_OUTLIERS = True in cleaner.py)

    All user-configurable options are in the CONFIG block at the top of this function.
    """
    try:
        data = Path(data)
        output = Path(output)
    except Exception as e:
        print(f"Error parsing directory to Path: {e}")

    # ============================================================
    # CONFIG — edit these values to control what the script does
    # ============================================================

    # Which study to run. Must match the STUDY setting used in plotter.py.
    #   1 = Erie / AJAX   (Dec 2024 – May 2025)
    #   2 = Boulder / ECC (Oct – Dec 2025)
    STUDY = 1

    # PM column to compare. Must exist in all selected instrument CSVs.
    #   'PM 2.5'  — fine particulate matter
    #   'PM 1.0'  — ultrafine particulate matter
    PM_COL = 'PM 2.5'

    # ============================================================
    # Load all cleaned CSVs and count outlier files
    # ============================================================
    df_by_name = {}
    outliers = {}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        warnings.simplefilter("ignore", category=FutureWarning)

        for csv in data.rglob("*.csv"):
            stem = csv.stem

            if stem.endswith("_outliers"):
                # Outlier files written by cleaner.py when FILTER_OUTLIERS = True.
                outliers[stem] = len(pd.read_csv(csv, low_memory=False))
                continue

            # Strip _cleaned suffix if present (cleaner.py appends it).
            base = stem[:-len("_cleaned")] if stem.endswith("_cleaned") else stem
            label = analysis.FILE_LABEL_MAP.get(base)
            if label is None:
                continue

            print("Reading", stem)
            df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])

            if df['time'].dt.tz is None:
                df['time'] = df['time'].dt.tz_localize('UTC')
            else:
                df['time'] = df['time'].dt.tz_convert('UTC')

            df_by_name[label] = df

    print()

    # ============================================================
    # Outlier counts
    # ============================================================
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        list(outliers.items()), columns=['Station Name', 'Number of Outliers']
    ).to_csv(output / "total_outliers.csv", index=False)

    # ============================================================
    # Pairwise hourly-average statistics
    # ============================================================
    all_labels = analysis.STUDY_LABELS[STUDY]

    prepped = {}
    for label in all_labels:
        df = df_by_name.get(label)
        if df is None:
            print(f"[WARN] No data found for {label}")
            continue
        hourly = analysis.prepare_hourly_df(df, PM_COL)
        if hourly is None:
            print(f"[WARN] {label} missing column '{PM_COL}'")
            continue
        prepped[label] = hourly
        print(f"[INFO] Prepared hourly data for {label}: {len(hourly)} hours")

    stats_results = {}

    for i, label1 in enumerate(all_labels):
        for label2 in all_labels[i+1:]:
            if label1 not in prepped or label2 not in prepped:
                continue

            merged = pd.merge(
                prepped[label1].rename(columns={PM_COL: 'val1'}),
                prepped[label2].rename(columns={PM_COL: 'val2'}),
                on='time',
                how='inner'
            ).dropna()

            if merged.empty:
                print(f"[INFO] No time overlap for {label1} vs {label2}.")
                continue

            is_outlier = (merged['val1'] > 50) | (merged['val2'] > 50)
            pair_stats = analysis.compute_pair_stats(
                merged['val1'].values, merged['val2'].values, is_outlier.values
            )
            stats_results[f"{label1} vs {label2}"] = pair_stats
            print(f"[INFO] Computed stats: {label1} vs {label2}")

    stats_df = pd.DataFrame(stats_results).T
    stats_df.to_csv(output / "pair_stats.csv")

    print()
    print(stats_df)


def parse_args():
    parser = argparse.ArgumentParser(description="Calculates statistical properties from data.")

    parser.add_argument("data",   type=str, help="The directory path where data is located.")
    parser.add_argument("output", type=str, help="The directory path where CSVs are to be saved.")

    args = parser.parse_args()

    return args.data, args.output


if __name__ == '__main__':
    main(*parse_args())
