import warnings
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import argparse


def main(data:str, output:str):
    """
    Reads cleaned CSVs, generates pairwise hourly-average scatter plots for all
    instrument combinations listed in all_labels, and prints comparison statistics.

    To switch between Study 1 (Erie/AJAX) and Study 2 (Boulder/ECC), update the
    all_labels list near the bottom of this function. See comments there for which
    labels belong to each study.

    To save plots to disk, uncomment the plt.savefig() call in _stats_and_scatter.
    To save the bias summary table, uncomment bias_df.to_csv() near the end.
    """
    try:
        data = Path(data)
        output = Path(output)
    except Exception as e:
        print(f"Error parsing directory: {e}")

    # ============================================================
    # Load all cleaned CSVs into dataframes
    # ============================================================
    dataframes = []
    names = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        warnings.simplefilter("ignore", category=FutureWarning)

        for csv in data.glob("*.csv"):
            name = str(csv.stem)
            print("Reading", name)

            if name.startswith("daily"):
                continue

            df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])

            # Ensure all timestamps are UTC so merges across sources align correctly.
            if df['time'].dt.tz is None:
                df['time'] = df['time'].dt.tz_localize('UTC')
            else:
                df['time'] = df['time'].dt.tz_convert('UTC')

            df['week'] = df['time'].dt.to_period('W')
            df['day']  = df['time'].dt.to_period('D')
            df['hour'] = df['time'].dt.to_period('H')

            # Uncomment this block to restrict all data to the Realization Fire window
            # (Nov 19 2025, 02:00–06:00 UTC) for the wildfire event deep-dive.
            # start_time = pd.Timestamp('2025-11-19 02:00:00', tz='UTC')
            # end_time   = pd.Timestamp('2025-11-19 06:00:00', tz='UTC')
            # df = df[(df['time'] >= start_time) & (df['time'] <= end_time)]

            df.set_index('time')
            dataframes.append(df)

            # Map raw file stems to human-readable labels used throughout the rest
            # of this script. If you add a new instrument, add a new elif here.
            # Study 1 — Erie / AJAX (Dec 2024 – May 2025):
            if name == '3D-PAWS_Instrument-16_2024-12-06_2025-05-12':
                names.append('3D-PAWS_AQ_Testbed')
            elif name == '3D-PAWS_Instrument-18_2024-12-06_2025-05-12':
                names.append('Payne Observation Site')
            elif name == '3D-PAWS_Instrument-127_2024-12-06_2025-05-12':
                names.append('AQ Comparison AJAX')
            elif name == 'UplandS_1min_S12.6.24_E5.12.25':
                names.append('AJAX Reference')
            # Study 2 — Boulder / ECC (Oct – Dec 2025):
            elif name == 'ECC_pm_complete':
                names.append('Erie Community Center Reference')
            elif name == '3D-PAWS_Instrument-153_2025-10-23_2025-12-09':
                names.append('AQ_Comparison_2')
            elif name == '3D-PAWS_Instrument-154_2025-10-23_2025-12-09':
                names.append('AQ_Comparison_1_5min')
            elif name == 'Marine Street 1 minute data_102325-120825':
                names.append('CU Boulder Reference')

    print()

    # ============================================================
    # OPTIONAL: Weekly time series plots (hourly averages)
    # Useful for visual data dropout assessment — gaps in the line
    # show where a sensor stopped reporting.
    # To enable: uncomment this entire block and update the names
    # filter list to match the study you're running.
    # ============================================================
    # with warnings.catch_warnings():
    #     warnings.simplefilter("ignore", category=pd.errors.SettingWithCopyWarning)
    #
    #     # Filter to only the stations relevant to the current study.
    #     # For Study 1 (Erie/AJAX), use ajax_names. For Study 2 (Boulder), use boulder_names.
    #     boulder_names = [
    #         n for n in names
    #         if n not in [
    #             '3D-PAWS_Instrument-16_2024-12-06_2025-05-12',
    #             '3D-PAWS_Instrument-18_2024-12-06_2025-05-12',
    #             '3D-PAWS_Instrument-127_2024-12-06_2025-05-12',
    #             'UplandS_1min_S12.6.24_E5.12.25',
    #             '3D-PAWS_Instrument-153_2025-10-23_2025-12-09'
    #         ]
    #     ]
    #
    #     cmap = plt.get_cmap('tab10')
    #     color_map = {name: cmap(i % cmap.N) for i, name in enumerate(sorted(set(boulder_names)))}
    #
    #     weeks = sorted(set().union(*(df['week'].unique() for df in dataframes)))
    #
    #     for week in weeks:
    #         week_str = str(week)
    #         plt.figure(figsize=(24, 12))
    #
    #         for i, df in enumerate(dataframes):
    #             weekly_df = df[df['week'] == week]
    #             if weekly_df.empty:
    #                 continue
    #
    #             weekly_df['time'] = pd.to_datetime(weekly_df['time'])
    #             weekly_df = weekly_df.set_index('time')
    #
    #             name = names[i]
    #             plt.plot(
    #                 weekly_df.index,
    #                 weekly_df['PM 2.5'],
    #                 label=f"{name} PM 2.5",
    #                 color=color_map[name]
    #             )
    #
    #         if not plt.gca().has_data():
    #             plt.close()
    #             continue
    #
    #         plt.xlabel("Time")
    #         plt.ylabel("PM 2.5 (µg/m³)")
    #         plt.title(f"{(week_str).replace('/',' to ')} PM 2.5")
    #         plt.legend()
    #         plt.grid(True)
    #         plt.tight_layout()
    #         plt.savefig(output / f"{week_str[:10]}-{week_str[11:]}_PM1s25_time-series.png")
    #         plt.clf()
    #         plt.close()


    # ============================================================
    # OPTIONAL: Daily average time series plots (one line per station)
    # Shows longer-term concentration trends. Point source:
    # set data= to raw/ for plots with outliers, cleaned/ for without.
    # ============================================================
    # for i, df in enumerate(dataframes):
    #     variable_list = ['PM 2.5']
    #
    #     daily_mean_df = df.groupby('day')[variable_list].mean()
    #     daily_mean_df.index = daily_mean_df.index.to_timestamp()
    #
    #     plt.figure(figsize=(12, 6))
    #     for var in variable_list:
    #         plt.plot(
    #             daily_mean_df.index,
    #             daily_mean_df[var],
    #             label=f"{var} Daily Mean"
    #         )
    #     plt.xlabel("Day")
    #     plt.ylabel("Particulate Concentration (µg/m³)")
    #     plt.title("Daily Average PM Variables Over Time")
    #     plt.legend()
    #     plt.grid(True)
    #     plt.tight_layout()
    #     plt.savefig(output / f"{names[i]}_daily_mean.png")
    #     plt.clf()
    #     plt.close()


    # ============================================================
    # Hourly-average scatter plots with statistics
    # ============================================================

    def calculate_slope(x, y):
        """Linear regression slope and intercept using polyfit."""
        if len(x) < 2:
            return np.nan
        slope, intercept = np.polyfit(x, y, 1)
        return slope, intercept


    def _prepare_hourly_df(df, col):
        """
        Convert timestamps to UTC-naive and resample to 1-hour averages.
        Returns None if col is not present in df.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)

            out = df.copy()
            if 'time' not in out.columns:
                out = out.reset_index()

            out['time'] = pd.to_datetime(out['time'], errors='coerce', utc=True).dt.tz_localize(None)
            if col not in out.columns:
                return None

            out[col] = pd.to_numeric(out[col], errors='coerce')
            out = out[['time', col]].dropna()
            out = out.set_index('time').resample('1H').mean().reset_index()
            return out.dropna()


    def _stats_and_scatter(x, y, is_outlier, xlabel, ylabel, title, savepath, num_points, lim=50):
        """
        Compute comparison statistics and generate a scatter plot.

        Statistics reported:
          slope/intercept — linear regression fit on cleaned (non-outlier) points only
          r               — Pearson correlation coefficient across all points
          RMSE            — root mean square error across all points
          overall_bias    — mean(y - x); positive means instrument reads HIGH vs reference
          bias_high/low   — bias split at 10 µg/m³ to capture regime-dependent behavior
                            (sensors often behave differently at low vs high concentrations)

        is_outlier: boolean array; True where either station exceeds 50 µg/m³.
                    Outlier points are shown in red; cleaned points in blue.

        lim: axis maximum for both x and y (default 50, active calls use 40).
        """
        r    = np.corrcoef(x, y)[0, 1] if len(x) > 1 else np.nan
        rmse = np.sqrt(np.mean((x - y) ** 2)) if len(x) > 0 else np.nan

        # Positive overall_bias means the y-axis instrument reads higher than x.
        overall_bias = np.mean(y - x) if len(x) > 0 else np.nan

        mask_high = (x > 10)
        mask_low  = (x <= 10)

        bias_high = np.mean(y[mask_high] - x[mask_high]) if np.sum(mask_high) > 0 else np.nan
        bias_low  = np.mean(y[mask_low] - x[mask_low]) if np.sum(mask_low) > 0 else np.nan

        n_high = np.sum(mask_high)
        n_low  = np.sum(mask_low)

        # Slope is computed on cleaned points only so outliers don't skew the fit line.
        clean_x = x[~is_outlier]
        clean_y = y[~is_outlier]
        slope, intercept = calculate_slope(clean_x, clean_y)

        plt.figure(figsize=(16, 16))
        plt.scatter(x[~is_outlier], y[~is_outlier],
                    color="blue", alpha=0.6, label="Cleaned (≤50 µg/m³)")
        plt.scatter(x[is_outlier], y[is_outlier],
                    color="red", alpha=0.8, label="Outlier (>50 µg/m³)")

        plt.plot([0, lim], [0, lim], 'k--', alpha=0.5, linewidth=1, label='1:1 line')

        ax = plt.gca()
        ax.set_aspect('equal', adjustable='box')
        plt.xlim(0, lim)
        plt.ylim(0, lim)
        plt.xlabel(xlabel, fontsize=20)
        plt.ylabel(ylabel, fontsize=20)
        plt.tick_params(axis='both', labelsize=16)
        plt.title(title, fontsize=24)
        plt.text(
            0.5, 36.35, f'Number of comparisons: {num_points}',
            fontsize=10, color='black', bbox=dict(facecolor='white', alpha=0.8, edgecolor='grey')
        )
        plt.grid(False)
        plt.legend()

        stats_text = (
            f"Slope = {slope:.3f}\n"
            f"Intercept = {intercept:3f}\n"
            f"r = {r:.2f}\n"
            f"RMSE = {rmse:.2f}\n"
            f"Overall Bias = {overall_bias:.2f}\n"
            f"\n"
            f"Bias (>10): {bias_high:.2f} (n={n_high})\n"
            f"Bias (≤10): {bias_low:.2f} (n={n_low})"
        )

        plt.text(
            0.23, 0.99, stats_text,
            transform=ax.transAxes, va='top',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='grey')
        )
        plt.tight_layout()

        # Uncomment to save plots to disk:
        # plt.savefig(savepath, dpi=200)

        print(stats_text)
        plt.close()

        return {
            'slope': slope,
            'intercept': intercept,
            'r': r,
            'rmse': rmse,
            'overall_bias': overall_bias,
            'bias_high': bias_high,
            'bias_low': bias_low,
            'n_high': n_high,
            'n_low': n_low
        }

    # Map labels to their corresponding dataframes for lookup below.
    df_by_name = {label: df for label, df in zip(names, dataframes)}

    # ----------------------------------------------------------------
    # TO CONFIGURE: list the instruments you want to compare.
    # The script generates all pairwise scatter plots from this list.
    #
    # Study 1 — Erie / AJAX (Dec 2024 – May 2025):
    #   'AJAX Reference', '3D-PAWS_AQ_Testbed', 'Payne Observation Site', 'AQ Comparison AJAX'
    #
    # Study 2 — Boulder / ECC (Oct – Dec 2025):
    #   'CU Boulder Reference', 'Erie Community Center Reference',
    #   'AQ_Comparison_2', 'AQ_Comparison_1_5min'
    #
    # Mix and match as needed. Only instruments in this list will be compared.
    # ----------------------------------------------------------------
    all_labels = [
        'Erie Community Center Reference',
        'AJAX Reference',
        '3D-PAWS_AQ_Testbed',
        'Payne Observation Site',
        'AQ Comparison AJAX'
        # 'CU Boulder Reference',
        # 'AQ_Comparison_2',
        # 'AQ_Comparison_1_5min'
    ]

    # TO CONFIGURE: ensure this column name exists in all instruments listed above.
    # 'PM 2.5' is the shared name after cleaning. Change to 'PM 1.0' for PM 1.0 comparisons.
    pm_col = 'PM 2.5'

    # Resample each instrument to hourly averages once, then reuse for all pairs.
    prepped_hourly_data = {}
    for label in all_labels:
        df = df_by_name.get(label, None)
        if df is None:
            print(f"[WARN] Could not find dataframe for {label}")
            continue

        prepped = _prepare_hourly_df(df, pm_col)
        if prepped is None:
            print(f"[WARN] {label} missing column '{pm_col}'")
            continue

        prepped_hourly_data[label] = prepped
        print(f"[INFO] Prepared hourly data for {label}: {len(prepped)} hours")

    output.mkdir(parents=True, exist_ok=True)

    bias_results = {}

    # Generate one scatter plot for every unique pair in all_labels.
    for i, label1 in enumerate(all_labels):
        for label2 in all_labels[i+1:]:
            if label1 not in prepped_hourly_data or label2 not in prepped_hourly_data:
                continue

            df1 = prepped_hourly_data[label1]
            df2 = prepped_hourly_data[label2]

            # Inner join on time: only hours where both instruments have data.
            merged = pd.merge(
                df1.rename(columns={pm_col: 'val1'}),
                df2.rename(columns={pm_col: 'val2'}),
                on='time',
                how='inner'
            ).dropna()

            num_datapoints = len(merged)

            if merged.empty:
                print(f"[INFO] No time overlap for {label1} vs {label2}.")
                continue

            # A point is an outlier if either instrument exceeds 50 µg/m³.
            merged['is_outlier'] = (merged['val1'] > 50) | (merged['val2'] > 50)

            fname = f"{pm_col}__{label1.replace(' ', '_')}__vs__{label2.replace(' ', '_')}__point.png"
            savepath = output / fname

            print(label1, "and", label2)
            stats = _stats_and_scatter(
                x=merged['val1'].values,
                y=merged['val2'].values,
                is_outlier=merged['is_outlier'].values,
                xlabel=f"{label1} {pm_col} (µg/m³)",
                ylabel=f"{label2} {pm_col} (µg/m³)",
                title=f"{pm_col}: {label1} vs {label2} Hourly Averages",
                savepath=savepath,
                num_points=num_datapoints,
                lim=40  # axis cap; outlier points beyond this are still plotted but clipped
            )

            bias_results[f"{label1} vs {label2}"] = stats

            print(f"[SUCCESS] Generated comparison: {label1} vs {label2}")
            print(f"  Overall Bias: {stats['overall_bias']:.2f}")
            print(f"  Bias (>10): {stats['bias_high']:.2f} (n={stats['n_high']})")
            print(f"  Bias (≤10): {stats['bias_low']:.2f} (n={stats['n_low']})")
            print()

    bias_df = pd.DataFrame(bias_results).T

    # Uncomment to save the bias summary table to CSV:
    # bias_df.to_csv(output / 'bias_summary.csv')

    print(f"[INFO] Bias summary (not saved — uncomment bias_df.to_csv to export):")
    print(bias_df)


    # ============================================================
    # OPTIONAL: Point-for-point scatter plots (minute-level, no hourly averaging)
    # Use this instead of the hourly block above when you want finer temporal
    # resolution. Instruments must share exact timestamps to produce matches,
    # so this works best when comparing 3D-PAWS instruments against each other.
    # For Study 2 CU Boulder comparisons, minute-level data is available for
    # Instrument 153 and CU Boulder but not for Instrument 154 (5-min intervals).
    # ============================================================
    # def _prepare_df(df, col):
    #     """Parse time, coerce numeric, return df with exact timestamps (no resampling)."""
    #     with warnings.catch_warnings():
    #         warnings.simplefilter("ignore", category=FutureWarning)
    #         out = df.copy()
    #         if 'time' not in out.columns:
    #             out = out.reset_index()
    #         out['time'] = pd.to_datetime(out['time'], errors='coerce', utc=True).dt.tz_localize(None)
    #         if col not in out.columns:
    #             return None
    #         out[col] = pd.to_numeric(out[col], errors='coerce')
    #         return out[['time', col]].dropna()
    #
    # df_by_name = {label: df for label, df in zip(names, dataframes)}
    #
    # # TO CONFIGURE: list the instruments for point-for-point comparison.
    # # Study 2 — Boulder example:
    # all_labels = [
    #     'CU Boulder Reference',
    #     'AQ_Comparison_2',
    #     'AQ_Comparison_1_5min'
    # ]
    # pm_col = 'PM 2.5'
    #
    # prepped_data = {}
    # for label in all_labels:
    #     df = df_by_name.get(label, None)
    #     if df is None:
    #         print(f"[WARN] Could not find dataframe for {label}")
    #         continue
    #     prepped = _prepare_df(df, pm_col)
    #     if prepped is None:
    #         print(f"[WARN] {label} missing column '{pm_col}'")
    #         continue
    #     prepped_data[label] = prepped
    #
    # output.mkdir(parents=True, exist_ok=True)
    #
    # for i, label1 in enumerate(all_labels):
    #     for label2 in all_labels[i+1:]:
    #         if label1 not in prepped_data or label2 not in prepped_data:
    #             continue
    #         merged = pd.merge(
    #             prepped_data[label1].rename(columns={pm_col: 'val1'}),
    #             prepped_data[label2].rename(columns={pm_col: 'val2'}),
    #             on='time',
    #             how='inner'
    #         ).dropna()
    #         num_datapoints = len(merged)
    #         if merged.empty:
    #             print(f"[INFO] No time overlap for {label1} vs {label2}.")
    #             continue
    #         merged['is_outlier'] = (merged['val1'] > 50) | (merged['val2'] > 50)
    #         fname = f"{pm_col}__{label1.replace(' ', '_')}__vs__{label2.replace(' ', '_')}__point.png"
    #         savepath = output / fname
    #         _stats_and_scatter(
    #             x=merged['val1'].values,
    #             y=merged['val2'].values,
    #             is_outlier=merged['is_outlier'].values,
    #             xlabel=f"{label1} {pm_col} (µg/m³)",
    #             ylabel=f"{label2} {pm_col} (µg/m³)",
    #             title=f"{pm_col}: {label1} vs {label2} (point-for-point)",
    #             savepath=savepath,
    #             num_points=num_datapoints,
    #             lim=40
    #         )
    #         print(f"[SUCCESS] Generated comparison: {label1} vs {label2}")


def parse_args():
    parser = argparse.ArgumentParser(description="Plotting for air quality sensor comparisons.")

    parser.add_argument("data",   type=str, help="Directory path where cleaned data is located.")
    parser.add_argument("output", type=str, help="Directory where plots should be outputted.")

    args = parser.parse_args()

    return args.data, args.output


if __name__ == '__main__':
    main(*parse_args())
