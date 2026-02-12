import warnings
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import argparse

"""
Intended to get pointed at any of the 3 data subfolders, raw/cleaned/outliers.
"""
def main(data:str, output:str):
    try:
        data = Path(data)
        output = Path(output)
    except Exception as e:
        print(f"Error parsing directory: {e}")


    """
    ========================================================================
    Dataframe generation 
    ========================================================================
    """
    dataframes = []
    names = []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        warnings.simplefilter("ignore", category=FutureWarning)

        for csv in data.glob("*.csv"):
            name = str(csv.stem)
            print("Reading", name)

            df = None
            if name.startswith("daily"): 
                continue
            else:
                df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])
                if df['time'].dt.tz is None:
                    df['time'] = df['time'].dt.tz_localize('UTC')
                else:
                    df['time'] = df['time'].dt.tz_convert('UTC')

            df['week'] = df['time'].dt.to_period('W')
            df['day']  = df['time'].dt.to_period('D')
            df['hour'] = df['time'].dt.to_period('H')

            # # truncate df for Realization Fire, comment this out to ignore
            # start_time = pd.Timestamp('2025-11-19 02:00:00', tz='UTC')
            # end_time   = pd.Timestamp('2025-11-19 06:00:00', tz='UTC')
            # df = df[(df['time'] >= start_time) & (df['time'] <= end_time)]

            df.set_index('time')

            dataframes.append(df)

            if name == '3D-PAWS_Instrument-16_2024-12-06_2025-05-12':
                names.append('3D-PAWS_AQ_Testbed')
            elif name == '3D-PAWS_Instrument-18_2024-12-06_2025-05-12':
                names.append('Payne Observation Site')
            elif name == '3D-PAWS_Instrument-127_2024-12-06_2025-05-12':
                names.append('AQ Comparison AJAX')
            elif name == 'ECC_pm_complete':
                names.append('Erie Community Center Reference')
            elif name == 'UplandS_1min_S12.6.24_E5.12.25':
                names.append('AJAX Reference')
            elif name == '3D-PAWS_Instrument-153_2025-10-23_2025-12-09':
                names.append('AQ_Comparison_2')
            elif name == '3D-PAWS_Instrument-154_2025-10-23_2025-12-09':
                names.append('AQ_Comparison_1_5min')
            elif name == 'Marine Street 1 minute data_102325-120825':
                names.append('CU Boulder Reference')

    print()

    """
    ========================================================================
    Weekly time series plots (hourly averages) for AJAX study in Erie
    ========================================================================
    """
    # with warnings.catch_warnings():
    #     warnings.simplefilter("ignore", category=pd.errors.SettingWithCopyWarning)

    #     # ajax_names = [   # skip CU Boulder AQ assessment, comment this out to ignore
    #     #     n for n in names
    #     #     if n not in [
    #     #         '3D-PAWS_Instrument-153_2025-10-23_2025-12-09',
    #     #         '3D-PAWS_Instrument-154_2025-10-23_2025-12-09',
    #     #         'daily_08_013_0003_2024_cleaned',
    #     #         'daily_08_013_0003_2025_cleaned',
    #     #         'Marine Street 1 minute data_102325-120825'
    #     #     ]
    #     # ]
    #     boulder_names = [   # skip Erie / AJAX assessment, comment out to ignore, update variable name
    #         n for n in names
    #         if n not in [
    #             '3D-PAWS_Instrument-16_2024-12-06_2025-05-12',
    #             '3D-PAWS_Instrument-18_2024-12-06_2025-05-12',
    #             '3D-PAWS_Instrument-127_2024-12-06_2025-05-12',
    #             'UplandS_1min_S12.6.24_E5.12.25',
    #             '3D-PAWS_Instrument-153_2025-10-23_2025-12-09'
    #         ]
    #     ]

    #     cmap = plt.get_cmap('tab10')  # or 'tab20', 'Set2', etc.
    #     color_map = {name: cmap(i % cmap.N) for i, name in enumerate(sorted(set(boulder_names)))} # <-------- UPDATE HERE

    #     weeks = sorted(set().union(*(df['week'].unique() for df in dataframes)))

    #     for week in weeks:
    #         week_str = str(week)
    #         plt.figure(figsize=(24, 12))

    #         for i, df in enumerate(dataframes):
    #             weekly_df = df[df['week'] == week]
    #             if weekly_df.empty:
    #                 continue

    #             weekly_df['time'] = pd.to_datetime(weekly_df['time'])
    #             weekly_df = weekly_df.set_index('time')

    #             # weekly_df_hourly_avg = (
    #             #     weekly_df
    #             #     .resample('H')
    #             #     .mean(numeric_only=True)
    #             #     .dropna(how='all')
    #             # )
    #             # if weekly_df_hourly_avg.empty:
    #             #     continue

    #             name = names[i]
    #             plt.plot(
    #                 # weekly_df_hourly_avg.index,
    #                 # weekly_df_hourly_avg['PM 2.5'],
    #                 weekly_df.index,
    #                 weekly_df['PM 2.5'],
    #                 label=f"{name} PM 2.5",
    #                 color=color_map[name]  # fixed color per instrument
    #             )

    #         if not plt.gca().has_data():
    #             plt.close()
    #             continue

    #         plt.xlabel("Time")
    #         plt.ylabel("PM 2.5 (µg/m³)")
    #         # plt.ylim(0, 50)
    #         plt.title(f"{(week_str).replace('/',' to ')} PM 2.5")
    #         plt.legend()
    #         plt.grid(True)
    #         plt.tight_layout()

    #         plt.savefig(output / f"{week_str[:10]}-{week_str[11:]}_PM1s25_time-series.png")
    #         plt.clf()
    #         plt.close()


    """
    ========================================================================
    Daily average time series plots
    ========================================================================
    """
    # with or without outliers (set data source cleaned vs raw and 
    # comment out portion in dataframe creation accordingly)

    # for i, df in enumerate(dataframes):
    #     variable_list = None
    #     if 'TVOC-Signal' in df.columns:
    #         variable_list = list(variable_mapper.values())
    #     else:
    #         variable_list = list(variable_mapper.keys())

    #     daily_mean_df = df.groupby('day')[variable_list].mean()
    #     daily_mean_df.index = daily_mean_df.index.to_timestamp()

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

    """
    ========================================================================
    1-hour and 24-hour average scatter plots [MISSING DAILY AGGREGATE]
    Fill in the all_labels list with the instruments to evaluate.
    Ensure pm_col uses shared column name across all instruments.
    ========================================================================
    """
    def calculate_slope(x, y):
        """Linear regression slope using polyfit."""
        if len(x) < 2:
            return np.nan
        slope, intercept = np.polyfit(x, y, 1)
        return slope, intercept


    def _prepare_hourly_df(df, col):
        """Parse time, coerce numeric, resample to hourly averages."""
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
            
            # Resample to hourly averages
            out = out.set_index('time').resample('1H').mean().reset_index()
            return out.dropna()
        

    def _stats_and_scatter(x, y, is_outlier, xlabel, ylabel, title, savepath, num_points, lim=50):
        r    = np.corrcoef(x, y)[0, 1] if len(x) > 1 else np.nan
        rmse = np.sqrt(np.mean((x - y) ** 2)) if len(x) > 0 else np.nan
        
        # Calculate overall bias (mean difference: y - x)
        # Positive bias means instrument reads HIGH compared to reference
        overall_bias = np.mean(y - x) if len(x) > 0 else np.nan
        
        # Calculate bias for values > 10 and < 10 (based on reference x values)
        mask_high = (x > 10)
        mask_low  = (x <= 10)
        
        bias_high = np.mean(y[mask_high] - x[mask_high]) if np.sum(mask_high) > 0 else np.nan
        bias_low  = np.mean(y[mask_low] - x[mask_low]) if np.sum(mask_low) > 0 else np.nan
        
        n_high = np.sum(mask_high)
        n_low  = np.sum(mask_low)

         # Calculate slope on CLEANED data only
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
        
        # stats_text = (
        #     f"r = {r:.2f}\n"
        #     f"RMSE = {rmse:.2f}\n"
        #     f"Overall Bias = {overall_bias:.2f}\n"
        #     f"\n"
        #     f"Bias (>10): {bias_high:.2f} (n={n_high})\n"
        #     f"Bias (≤10): {bias_low:.2f} (n={n_low})"
        # )
        stats_text = (
            f"Slope = {slope:.3f}\n"      # <-- NEW LINE
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
        # plt.savefig(savepath, dpi=200)
        print(stats_text)
        plt.close()
        
        # return {
        #     'r': r,
        #     'rmse': rmse,
        #     'overall_bias': overall_bias,
        #     'bias_high': bias_high,
        #     'bias_low': bias_low,
        #     'n_high': n_high,
        #     'n_low': n_low
        # }
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

    # Map labels to dataframes
    df_by_name = {label: df for label, df in zip(names, dataframes)}

    all_labels = [ #                                        <-------- FILL THIS IN
        'Erie Community Center Reference',
        'AJAX Reference',        
        '3D-PAWS_AQ_Testbed',
        'Payne Observation Site',
        'AQ Comparison AJAX'
        # 'CU Boulder Reference',
        # 'AQ_Comparison_2',
        # 'AQ_Comparison_1_5min'
    ]

    pm_col = 'PM 2.5' #                                     <-------- MAKE SURE THIS IS CORRECT

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

    for i, label1 in enumerate(all_labels):
        for label2 in all_labels[i+1:]:
            if label1 not in prepped_hourly_data or label2 not in prepped_hourly_data:
                continue
            
            df1 = prepped_hourly_data[label1]
            df2 = prepped_hourly_data[label2]
            
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
                lim=40
            )
            
            bias_results[f"{label1} vs {label2}"] = stats
            
            print(f"[SUCCESS] Generated comparison: {label1} vs {label2}")
            print(f"  Overall Bias: {stats['overall_bias']:.2f}")
            print(f"  Bias (>10): {stats['bias_high']:.2f} (n={stats['n_high']})")
            print(f"  Bias (≤10): {stats['bias_low']:.2f} (n={stats['n_low']})")
            print()

    bias_df = pd.DataFrame(bias_results).T
    # bias_df.to_csv(output / 'bias_summary.csv')
    print(f"[INFO] Bias summary saved to {output / 'bias_summary.csv'}")

    
    # # FOR POINT-FOR-POINT ---------------------------------------------------------------
    # def _prepare_df(df, col):
    #     """Parse time, coerce numeric, return df with time + value only."""
    #     with warnings.catch_warnings():
    #         warnings.simplefilter("ignore", category=FutureWarning)

    #         out = df.copy()
    #         if 'time' not in out.columns:
    #             out = out.reset_index()

    #         out['time'] = pd.to_datetime(out['time'], errors='coerce', utc=True).dt.tz_localize(None)
    #         if col not in out.columns:
    #             return None

    #         out[col] = pd.to_numeric(out[col], errors='coerce')
    #         # Keep exact timestamps for point‑for‑point comparison
    #         return out[['time', col]].dropna()

    # def _stats_and_scatter(x, y, is_outlier, xlabel, ylabel, title, savepath, num_points, lim=50):
    #     r = np.corrcoef(x, y)[0, 1] if len(x) > 1 else np.nan
    #     rmse = np.sqrt(np.mean((x - y) ** 2)) if len(x) > 0 else np.nan

    #     plt.figure(figsize=(12, 12))
    #     plt.scatter(x[~is_outlier], y[~is_outlier],
    #                 color="blue", alpha=0.6, label="Cleaned (≤50 µg/m³)")
    #     plt.scatter(x[is_outlier], y[is_outlier],
    #                 color="red", alpha=0.8, label="Outlier (>50 µg/m³)")

    #     ax = plt.gca()
    #     ax.set_aspect('equal', adjustable='box')
    #     plt.xlim(0, lim)
    #     plt.ylim(0, lim)
    #     plt.xlabel(xlabel)
    #     plt.ylabel(ylabel)
    #     plt.title(title)
    #     plt.text(1, 36, f'Number of comparisons: {num_points}', fontsize=10, color='black')
    #     plt.grid(True)
    #     plt.legend()
    #     plt.text(0.03, 0.97, f"r = {r:.2f}\nRMSE = {rmse:.2f}",
    #              transform=ax.transAxes, va='top',
    #              bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
    #     plt.tight_layout()
    #     plt.savefig(savepath, dpi=200)
    #     plt.close()

    # # Map labels to dataframes
    # df_by_name = {label: df for label, df in zip(names, dataframes)}

    # erie_label = 'CU Boulder Reference'
    # compare_labels = [
    #     'AQ_Comparison_2',
    #     'AQ_Comparison_1_5min'
    # ]

    # erie_col = 'PM 2.5'
    # site_col = 'PM 2.5'

    # erie_df = df_by_name.get(erie_label, None)
    # if erie_df is None:
    #     print(f"[ERROR] Could not find dataframe for {erie_label}")
    #     return

    # erie_prepped = _prepare_df(erie_df, erie_col)
    # if erie_prepped is None:
    #     print(f"[ERROR] {erie_label} missing column '{erie_col}'")
    #     return

    # output.mkdir(parents=True, exist_ok=True)

    # for site_label in compare_labels:
    #     site_df = df_by_name.get(site_label, None)
    #     if site_df is None:
    #         print(f"[WARN] No dataframe found for {site_label}, skipping.")
    #         continue

    #     site_prepped = _prepare_df(site_df, site_col)
    #     if site_prepped is None:
    #         print(f"[WARN] {site_label} missing column '{site_col}', skipping.")
    #         continue

    #     # Point‑for‑point merge on exact timestamps
    #     merged = pd.merge(
    #         erie_prepped.rename(columns={erie_col: 'erie_val'}),
    #         site_prepped.rename(columns={site_col: 'site_val'}),
    #         on='time',
    #         how='inner'
    #     ).dropna()

    #     num_datapoints = len(merged)

    #     if merged.empty:
    #         print(f"[INFO] No time overlap for {erie_label} vs {site_label}.")
    #         continue

    #     # Outliers defined on Erie; threshold 50
    #     merged['is_outlier'] = merged['erie_val'] > 50

    #     fname = f"{erie_col}__{erie_label.replace(' ', '_')}__vs__{site_label.replace(' ', '_')}__point.png"
    #     savepath = output / fname

    #     _stats_and_scatter(
    #         x=merged['erie_val'].values,       # Erie on x-axis
    #         y=merged['site_val'].values,       # comparison site on y-axis
    #         is_outlier=merged['is_outlier'].values,
    #         xlabel=f"{erie_label} {erie_col} (µg/m³)",
    #         ylabel=f"{site_label} {site_col} (µg/m³)",
    #         title=f"{erie_col}: {erie_label} vs {site_label} (point-for-point)",
    #         savepath=savepath,
    #         num_points=num_datapoints,
    #         lim=40
    #     )

#    # FOR POINT-FOR-POINT
#     def _prepare_df(df, col):
#         """Parse time, coerce numeric, return df with time + value only."""
#         with warnings.catch_warnings():
#             warnings.simplefilter("ignore", category=FutureWarning)

#             out = df.copy()
#             if 'time' not in out.columns:
#                 out = out.reset_index()

#             out['time'] = pd.to_datetime(out['time'], errors='coerce', utc=True).dt.tz_localize(None)
#             if col not in out.columns:
#                 return None

#             out[col] = pd.to_numeric(out[col], errors='coerce')
#             return out[['time', col]].dropna()

#     def _stats_and_scatter(x, y, is_outlier, xlabel, ylabel, title, savepath, num_points, lim=50):
#         r = np.corrcoef(x, y)[0, 1] if len(x) > 1 else np.nan
#         rmse = np.sqrt(np.mean((x - y) ** 2)) if len(x) > 0 else np.nan

#         plt.figure(figsize=(12, 12))
#         plt.scatter(x[~is_outlier], y[~is_outlier],
#                     color="blue", alpha=0.6, label="Cleaned (≤50 µg/m³)")
#         plt.scatter(x[is_outlier], y[is_outlier],
#                     color="red", alpha=0.8, label="Outlier (>50 µg/m³)")

#         ax = plt.gca()
#         ax.set_aspect('equal', adjustable='box')
#         plt.xlim(0, lim)
#         plt.ylim(0, lim)
#         plt.xlabel(xlabel)
#         plt.ylabel(ylabel)
#         plt.title(title)
#         plt.text(1, 36, f'Number of comparisons: {num_points}', fontsize=10, color='black')
#         plt.grid(True)
#         plt.legend()
#         plt.text(0.03, 0.97, f"r = {r:.2f}\nRMSE = {rmse:.2f}",
#                 transform=ax.transAxes, va='top',
#                 bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
#         plt.tight_layout()
#         plt.savefig(savepath, dpi=200)
#         plt.close()

#     # Map labels to dataframes
#     df_by_name = {label: df for label, df in zip(names, dataframes)}

#     all_labels = [
#         'CU Boulder Reference',
#         'AQ_Comparison_2',
#         'AQ_Comparison_1_5min'
#     ]

#     pm_col = 'PM 2.5'

#     # Prepare all dataframes once
#     prepped_data = {}
#     for label in all_labels:
#         df = df_by_name.get(label, None)
#         if df is None:
#             print(f"[WARN] Could not find dataframe for {label}")
#             continue
        
#         prepped = _prepare_df(df, pm_col)
#         if prepped is None:
#             print(f"[WARN] {label} missing column '{pm_col}'")
#             continue
        
#         prepped_data[label] = prepped

#     output.mkdir(parents=True, exist_ok=True)

#     # Generate all pairwise comparisons
#     for i, label1 in enumerate(all_labels):
#         for label2 in all_labels[i+1:]:  # Only compare each pair once
#             if label1 not in prepped_data or label2 not in prepped_data:
#                 continue
            
#             df1 = prepped_data[label1]
#             df2 = prepped_data[label2]
            
#             # Point-for-point merge on exact timestamps
#             merged = pd.merge(
#                 df1.rename(columns={pm_col: 'val1'}),
#                 df2.rename(columns={pm_col: 'val2'}),
#                 on='time',
#                 how='inner'
#             ).dropna()
            
#             num_datapoints = len(merged)
            
#             if merged.empty:
#                 print(f"[INFO] No time overlap for {label1} vs {label2}.")
#                 continue
            
#             # Outliers defined on first dataset (x-axis); threshold 50
#             merged['is_outlier'] = merged['val1'] > 50
            
#             fname = f"{pm_col}__{label1.replace(' ', '_')}__vs__{label2.replace(' ', '_')}__point.png"
#             savepath = output / fname
            
#             _stats_and_scatter(
#                 x=merged['val1'].values,
#                 y=merged['val2'].values,
#                 is_outlier=merged['is_outlier'].values,
#                 xlabel=f"{label1} {pm_col} (µg/m³)",
#                 ylabel=f"{label2} {pm_col} (µg/m³)",
#                 title=f"{pm_col}: {label1} vs {label2} (point-for-point)",
#                 savepath=savepath,
#                 num_points=num_datapoints,
#                 lim=40
#             )
            
#             print(f"[SUCCESS] Generated comparison: {label1} vs {label2}")


def parse_args():
    parser = argparse.ArgumentParser(description="Plotting for air quality sensor comparisons.")

    parser.add_argument("data", type=str, help="Directory path where data is located.")
    parser.add_argument("output", type=str, help="Directory where plots should be outputted.")

    args = parser.parse_args()

    return args.data, args.output


if __name__ == '__main__':
    main(*parse_args())
