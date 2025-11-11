import warnings
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import argparse

def main(data:str, output:str):
    try:
        data = Path(data)
        output = Path(output)
    except Exception as e:
        print(f"Error parsing directory: {e}")

    names = ['Payne Obs. Site', 'AJAX Reference', 'AQI Testbed', 'AJAX Co-Located']

    variable_mapper = { # 3D-PAWS : AJAX co-located site
        'pm1s10':'PM 1.0',
        'pm1s25':'PM 2.5',
        'pm1e10':'PM 1.0',
        'pm1e25':'PM 2.5'
    }

    """
    ========================================================================
    Dataframe generation 
    ========================================================================
    """
    dataframes = []
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)

        i = 0
        for csv in data.glob("*.csv"):
            print("Reading", str(csv.name))

            df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])
            df['week'] = df['time'].dt.to_period('W')
            df.set_index('time')
            dataframes.append(df)

            i += 1

    print()

    """
    ========================================================================
    Weekly time series plots
    ========================================================================
    """
    weeks = sorted(set().union(*(df['week'].unique() for df in dataframes)))

    for week in weeks:
        week = str(week)

        for var_3dpaws, var_ajax in variable_mapper.items():
            plt.figure(figsize=(12, 6))

            for i, df in enumerate(dataframes):
                weekly_df = df[df['week'] == week]

                if weekly_df.empty: continue

                if "TVOC-Signal" in list(df.columns): # AJAX site
                    plt.plot(
                            weekly_df['time'],
                            weekly_df[var_ajax],
                            label=f"AJAX Reference ({var_ajax})"
                        )
                else: # 3D-PAWS
                    plt.plot(
                            weekly_df['time'],
                            weekly_df[var_3dpaws],
                            label=f"3D-PAWS {names[i]} ({var_3dpaws})"
                        )

            plt.xlabel("Time")
            plt.ylabel(f"{var_ajax} (µg/m³)")
            plt.ylim(0, 50)
            plt.title(f"{week} {var_ajax} 3D-PAWS versus AJAX")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()

            safe_var_name = var_ajax.replace(" ", "-").replace(".", "_")
            plt.savefig(output / f"{week[:10]}-{week[11:]}_{safe_var_name}_time-series.png")

            plt.clf()
            plt.close()


    """
    ========================================================================
    1-hour and 24-hour average scatter plots
    ========================================================================
    """
    def _prepare_df(df, col):
        """Parse time, coerce numeric, add hour/day keys, return df with needed cols only."""
        out = df.copy()
        out['time'] = pd.to_datetime(out['time'], errors='coerce', utc=True).dt.tz_localize(None)
        if col not in out.columns:
            return None
        out[col] = pd.to_numeric(out[col], errors='coerce')
        out['hour_key'] = out['time'].dt.floor('H')
        out['day_key']  = out['time'].dt.floor('D')
        return out[['hour_key','day_key', col]]


    def _agg_on_key(df, col, key, newname):
        """Group by time key and mean."""
        return (df.groupby(key)[col].mean()
                    .rename(newname)
                    .reset_index())


    def _stats_and_scatter(x, y, xlabel, ylabel, title, savepath, lim=50):
        r = np.corrcoef(x, y)[0, 1] if len(x) > 1 else np.nan
        rmse = np.sqrt(np.mean((x - y) ** 2)) if len(x) > 0 else np.nan

        plt.figure(figsize=(12, 12))
        plt.scatter(x, y, alpha=0.6)
        # plt.plot([0, lim],[0, lim], linewidth=1)  # 1:1 line

        ax = plt.gca()
        ax.set_aspect('equal', adjustable='box')
        plt.xlim(0, lim); plt.ylim(0, lim)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.grid(True)
        # Place text box in top-left (axes coords)
        plt.text(0.03, 0.97, f"r = {r:.2f}\nRMSE = {rmse:.2f}",
                    transform=ax.transAxes, va='top',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
        plt.tight_layout()
        plt.savefig(savepath, dpi=200)
        plt.close()

    # Identify AJAX and PAWS frames
    def _is_ajax(df):
        if 'TVOC-Signal' in df.columns: return True
        return False
        # return ('TVOC-Signal' in df.columns) # or ('PM 2.5' in df.columns)


    ajax_idx = next((i for i, df in enumerate(dataframes) if _is_ajax(df)), None)
    if ajax_idx is None:
        raise RuntimeError("Could not find AJAX dataframe; check your _is_ajax() heuristic.")

    ajax_df = dataframes[ajax_idx]
    ajax_name = names[ajax_idx]

    paws_idxs = [i for i in range(len(dataframes)) if i != ajax_idx]
    paws_dfs  = [dataframes[i] for i in paws_idxs]
    paws_names= [names[i] for i in paws_idxs]

    # --- MAIN LOOP: one scatter per PAWS vs AJAX per variable (hourly & daily) ---
    for var_3dpaws, var_ajax in variable_mapper.items():
        # prepare AJAX once for both time scales
        ajax_prepped = _prepare_df(ajax_df, var_ajax)
        if ajax_prepped is None:
            print(f"[WARN] AJAX missing column '{var_ajax}', skipping.")
            continue
        ajax_hour = _agg_on_key(ajax_prepped, var_ajax, 'hour_key', 'ajax_val')
        ajax_day  = _agg_on_key(ajax_prepped, var_ajax, 'day_key',  'ajax_val')

        for paws_df, paws_label in zip(paws_dfs, paws_names):
            paws_prepped = _prepare_df(paws_df, var_3dpaws)
            if paws_prepped is None:
                print(f"[WARN] {paws_label} missing column '{var_3dpaws}', skipping.")
                continue

            # --- Hourly ---
            paws_hour = _agg_on_key(paws_prepped, var_3dpaws, 'hour_key', 'paws_val')
            merged_h = pd.merge(paws_hour, ajax_hour, on='hour_key', how='inner').dropna()
            if not merged_h.empty:
                _stats_and_scatter(
                    x=merged_h['paws_val'].values,
                    y=merged_h['ajax_val'].values,
                    xlabel=f"{paws_label} {var_3dpaws} Hourly Avg (µg/m³)",
                    ylabel=f"{ajax_name} {var_ajax} Hourly Avg (µg/m³)",
                    title=f"Hourly {var_ajax}: {paws_label} vs {ajax_name}",
                    savepath=output / f"{var_3dpaws}__{paws_label}__vs__{ajax_name}__hourly.png",
                    lim=40
                )
            else:
                print(f"[INFO] No hourly overlap for {paws_label} vs {ajax_name} ({var_3dpaws} vs {var_ajax}).")

            # --- Daily ---
            paws_day = _agg_on_key(paws_prepped, var_3dpaws, 'day_key', 'paws_val')
            merged_d = pd.merge(paws_day, ajax_day, on='day_key', how='inner').dropna()
            if not merged_d.empty:
                _stats_and_scatter(
                    x=merged_d['paws_val'].values,
                    y=merged_d['ajax_val'].values,
                    xlabel=f"{paws_label} {var_3dpaws} Daily Avg (µg/m³)",
                    ylabel=f"{ajax_name} {var_ajax} Daily Avg (µg/m³)",
                    title=f"Daily {var_ajax}: {paws_label} vs {ajax_name}",
                    savepath=output / f"{var_3dpaws}__{paws_label}__vs__{ajax_name}__daily.png",
                    lim=40
                )
            else:
                print(f"[INFO] No daily overlap for {paws_label} vs {ajax_name} ({var_3dpaws} vs {var_ajax}).")


def parse_args():
    parser = argparse.ArgumentParser(description="Plotting for air quality sensor comparisons.")

    parser.add_argument("data", type=str, help="Directory path where data is located.")
    parser.add_argument("output", type=str, help="Directory where plots should be outputted.")

    args = parser.parse_args()

    return args.data, args.output


if __name__ == '__main__':
    main(*parse_args())
