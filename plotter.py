import warnings
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import argparse
import analysis


def main(data:str, output:str):
    """
    Reads cleaned CSVs, generates pairwise hourly-average scatter plots for all
    instruments in the selected study, and prints comparison statistics.

    All user-configurable options are in the CONFIG block at the top of this function.
    """
    try:
        data = Path(data)
        output = Path(output)
    except Exception as e:
        print(f"Error parsing directory: {e}")

    # ============================================================
    # CONFIG — edit these values to control what the script does
    # ============================================================

    # Which study to run. Controls which instruments are compared.
    #   1 = Erie / AJAX   (Dec 2024 – May 2025)
    #   2 = Boulder / ECC (Oct – Dec 2025)
    STUDY = 1

    # PM column to compare. Must exist in all selected instrument CSVs.
    #   'PM 2.5'  — fine particulate matter
    #   'PM 1.0'  — ultrafine particulate matter
    PM_COL = 'PM 2.5'

    # Save hourly scatter plots to the output directory.
    SAVE_PLOTS = True

    # Save the bias summary table to output/bias_summary.csv.
    SAVE_BIAS_CSV = False

    # Generate weekly hourly-average time series plots (useful for spotting data gaps).
    PLOT_WEEKLY_TIMESERIES = False

    # Generate daily-average time series plots (one line per instrument).
    PLOT_DAILY_AVERAGES = False

    # Generate point-for-point (minute-level) scatter plots instead of hourly averages.
    # Works best when comparing 3D-PAWS instruments against each other; instruments
    # must share exact timestamps to produce matches.
    # Note: for Study 2, minute-level data is only available for Instrument 153 and
    # CU Boulder — Instrument 154 uses 5-min intervals.
    PLOT_POINT_FOR_POINT = False

    # Restrict all data to the Realization Fire window (Nov 19 2025, 02:00–06:00 UTC).
    FILTER_REALIZATION_FIRE = False

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

            label = analysis.FILE_LABEL_MAP.get(name)
            if label is None:
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

            if FILTER_REALIZATION_FIRE:
                start_time = pd.Timestamp('2025-11-19 02:00:00', tz='UTC')
                end_time   = pd.Timestamp('2025-11-19 06:00:00', tz='UTC')
                df = df[(df['time'] >= start_time) & (df['time'] <= end_time)]

            df.set_index('time')
            dataframes.append(df)
            names.append(label)

    print()

    df_by_name = {label: df for label, df in zip(names, dataframes)}

    # ============================================================
    # Scatter plot with statistics (plotting-only wrapper)
    # ============================================================

    def _stats_and_scatter(x, y, is_outlier, xlabel, ylabel, title, savepath, num_points, lim=50):
        """
        Compute comparison statistics and generate a scatter plot.

        Delegates all stat computation to analysis.compute_pair_stats.
        is_outlier: True where either station exceeds 50 µg/m³ — outlier points shown in red.
        lim: axis maximum for both x and y (default 50, active calls use 40).
        """
        stats = analysis.compute_pair_stats(x, y, is_outlier)

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
            f"Slope = {stats['slope']:.3f}\n"
            f"Intercept = {stats['intercept']:3f}\n"
            f"r = {stats['r']:.2f}\n"
            f"RMSE = {stats['rmse']:.2f}\n"
            f"Overall Bias = {stats['overall_bias']:.2f}\n"
            f"\n"
            f"Bias (>10): {stats['bias_high']:.2f} (n={stats['n_high']})\n"
            f"Bias (≤10): {stats['bias_low']:.2f} (n={stats['n_low']})"
        )

        plt.text(
            0.23, 0.99, stats_text,
            transform=ax.transAxes, va='top',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='grey')
        )
        plt.tight_layout()

        if SAVE_PLOTS:
            plt.savefig(savepath, dpi=200)

        print(stats_text)
        plt.close()

        return stats

    # ============================================================
    # OPTIONAL: Weekly time series plots (hourly averages)
    # Useful for visual data dropout assessment — gaps in the line
    # show where a sensor stopped reporting.
    # Enable by setting PLOT_WEEKLY_TIMESERIES = True in CONFIG.
    # ============================================================
    if PLOT_WEEKLY_TIMESERIES:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=pd.errors.SettingWithCopyWarning)

            study_names = analysis.STUDY_LABELS[STUDY]
            cmap = plt.get_cmap('tab10')
            color_map = {name: cmap(i % cmap.N) for i, name in enumerate(sorted(set(study_names)))}

            weeks = sorted(set().union(*(df['week'].unique() for df in dataframes)))

            for week in weeks:
                week_str = str(week)
                plt.figure(figsize=(24, 12))

                for i, df in enumerate(dataframes):
                    if names[i] not in study_names:
                        continue
                    weekly_df = df[df['week'] == week]
                    if weekly_df.empty:
                        continue

                    weekly_df['time'] = pd.to_datetime(weekly_df['time'])
                    weekly_df = weekly_df.set_index('time')

                    name = names[i]
                    plt.plot(
                        weekly_df.index,
                        weekly_df[PM_COL],
                        label=f"{name} {PM_COL}",
                        color=color_map[name]
                    )

                if not plt.gca().has_data():
                    plt.close()
                    continue

                plt.xlabel("Time")
                plt.ylabel(f"{PM_COL} (µg/m³)")
                plt.title(f"{(week_str).replace('/', ' to ')} {PM_COL}")
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                output.mkdir(parents=True, exist_ok=True)
                plt.savefig(output / f"{week_str[:10]}-{week_str[11:]}_{PM_COL.replace(' ', '_')}_time-series.png")
                plt.clf()
                plt.close()

    # ============================================================
    # OPTIONAL: Daily average time series plots (one line per station)
    # Shows longer-term concentration trends.
    # Enable by setting PLOT_DAILY_AVERAGES = True in CONFIG.
    # ============================================================
    if PLOT_DAILY_AVERAGES:
        study_names = analysis.STUDY_LABELS[STUDY]
        for i, df in enumerate(dataframes):
            if names[i] not in study_names:
                continue

            daily_mean_df = df.groupby('day')[[PM_COL]].mean()
            daily_mean_df.index = daily_mean_df.index.to_timestamp()

            plt.figure(figsize=(12, 6))
            plt.plot(daily_mean_df.index, daily_mean_df[PM_COL], label=f"{PM_COL} Daily Mean")
            plt.xlabel("Day")
            plt.ylabel("Particulate Concentration (µg/m³)")
            plt.title(f"Daily Average {PM_COL} — {names[i]}")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            output.mkdir(parents=True, exist_ok=True)
            plt.savefig(output / f"{names[i]}_daily_mean.png")
            plt.clf()
            plt.close()

    # ============================================================
    # Hourly-average scatter plots with statistics
    # ============================================================
    all_labels = analysis.STUDY_LABELS[STUDY]

    prepped_hourly_data = {}
    for label in all_labels:
        df = df_by_name.get(label, None)
        if df is None:
            print(f"[WARN] Could not find dataframe for {label}")
            continue

        prepped = analysis.prepare_hourly_df(df, PM_COL)
        if prepped is None:
            print(f"[WARN] {label} missing column '{PM_COL}'")
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
                df1.rename(columns={PM_COL: 'val1'}),
                df2.rename(columns={PM_COL: 'val2'}),
                on='time',
                how='inner'
            ).dropna()

            num_datapoints = len(merged)

            if merged.empty:
                print(f"[INFO] No time overlap for {label1} vs {label2}.")
                continue

            # A point is an outlier if either instrument exceeds 50 µg/m³.
            merged['is_outlier'] = (merged['val1'] > 50) | (merged['val2'] > 50)

            fname = f"{PM_COL}__{label1.replace(' ', '_')}__vs__{label2.replace(' ', '_')}__point.png"
            savepath = output / fname

            print(label1, "and", label2)
            stats = _stats_and_scatter(
                x=merged['val1'].values,
                y=merged['val2'].values,
                is_outlier=merged['is_outlier'].values,
                xlabel=f"{label1} {PM_COL} (µg/m³)",
                ylabel=f"{label2} {PM_COL} (µg/m³)",
                title=f"{PM_COL}: {label1} vs {label2} Hourly Averages",
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

    if SAVE_BIAS_CSV:
        bias_df.to_csv(output / 'bias_summary.csv')
        print(f"[INFO] Bias summary saved to {output / 'bias_summary.csv'}")
    else:
        print(f"[INFO] Bias summary (set SAVE_BIAS_CSV = True to export):")
        print(bias_df)

    # ============================================================
    # OPTIONAL: Point-for-point scatter plots (minute-level, no hourly averaging)
    # Enable by setting PLOT_POINT_FOR_POINT = True in CONFIG.
    # ============================================================
    if PLOT_POINT_FOR_POINT:
        prepped_data = {}
        for label in all_labels:
            df = df_by_name.get(label, None)
            if df is None:
                print(f"[WARN] Could not find dataframe for {label}")
                continue
            prepped = analysis.prepare_df(df, PM_COL)
            if prepped is None:
                print(f"[WARN] {label} missing column '{PM_COL}'")
                continue
            prepped_data[label] = prepped

        for i, label1 in enumerate(all_labels):
            for label2 in all_labels[i+1:]:
                if label1 not in prepped_data or label2 not in prepped_data:
                    continue
                merged = pd.merge(
                    prepped_data[label1].rename(columns={PM_COL: 'val1'}),
                    prepped_data[label2].rename(columns={PM_COL: 'val2'}),
                    on='time',
                    how='inner'
                ).dropna()
                num_datapoints = len(merged)
                if merged.empty:
                    print(f"[INFO] No time overlap for {label1} vs {label2}.")
                    continue
                merged['is_outlier'] = (merged['val1'] > 50) | (merged['val2'] > 50)
                fname = f"{PM_COL}__{label1.replace(' ', '_')}__vs__{label2.replace(' ', '_')}__point-for-point.png"
                savepath = output / fname
                _stats_and_scatter(
                    x=merged['val1'].values,
                    y=merged['val2'].values,
                    is_outlier=merged['is_outlier'].values,
                    xlabel=f"{label1} {PM_COL} (µg/m³)",
                    ylabel=f"{label2} {PM_COL} (µg/m³)",
                    title=f"{PM_COL}: {label1} vs {label2} (point-for-point)",
                    savepath=savepath,
                    num_points=num_datapoints,
                    lim=40
                )
                print(f"[SUCCESS] Generated comparison: {label1} vs {label2}")


def parse_args():
    parser = argparse.ArgumentParser(description="Plotting for air quality sensor comparisons.")

    parser.add_argument("data",   type=str, help="Directory path where cleaned data is located.")
    parser.add_argument("output", type=str, help="Directory where plots should be outputted.")

    args = parser.parse_args()

    return args.data, args.output


if __name__ == '__main__':
    main(*parse_args())
