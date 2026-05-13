import warnings
import numpy as np
import pandas as pd


# Instrument labels for each study. Used by both plotter.py and stats.py.
STUDY_LABELS = {
    1: [
        'AJAX Reference',
        '3D-PAWS_AQ_Testbed',
        'Payne Observation Site',
        'AQ Comparison AJAX',
    ],
    2: [
        'CU Boulder Reference',
        'Erie Community Center Reference',
        'AQ_Comparison_2',
        'AQ_Comparison_1_5min',
    ],
}

# Maps raw CSV file stems (as produced by cleaner.py) to human-readable labels.
# Add a new entry here whenever a new instrument is added to either study.
FILE_LABEL_MAP = {
    '3D-PAWS_Instrument-16_2024-12-06_2025-05-12':  '3D-PAWS_AQ_Testbed',
    '3D-PAWS_Instrument-18_2024-12-06_2025-05-12':  'Payne Observation Site',
    '3D-PAWS_Instrument-127_2024-12-06_2025-05-12': 'AQ Comparison AJAX',
    'UplandS_1min_S12.6.24_E5.12.25':               'AJAX Reference',
    'ECC_pm_complete':                               'Erie Community Center Reference',
    '3D-PAWS_Instrument-153_2025-10-23_2025-12-09': 'AQ_Comparison_2',
    '3D-PAWS_Instrument-154_2025-10-23_2025-12-09': 'AQ_Comparison_1_5min',
    'Marine Street 1 minute data_102325-120825':     'CU Boulder Reference',
}


def _slope_intercept(x, y):
    if len(x) < 2:
        return np.nan, np.nan
    return np.polyfit(x, y, 1)


def prepare_hourly_df(df, col):
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


def prepare_df(df, col):
    """Parse time and coerce numeric; returns df with exact timestamps (no resampling)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FutureWarning)
        out = df.copy()
        if 'time' not in out.columns:
            out = out.reset_index()
        out['time'] = pd.to_datetime(out['time'], errors='coerce', utc=True).dt.tz_localize(None)
        if col not in out.columns:
            return None
        out[col] = pd.to_numeric(out[col], errors='coerce')
        return out[['time', col]].dropna()


def compute_pair_stats(x, y, is_outlier):
    """
    Compute comparison statistics between two co-located instrument arrays.

    x, y        -- aligned numpy arrays of PM concentrations
    is_outlier  -- boolean array; True where either station exceeds 50 µg/m³

    Returns a dict with:
      slope, intercept  -- linear fit on cleaned (non-outlier) points only
      r                 -- Pearson correlation across all points
      rmse              -- root mean square error across all points
      overall_bias      -- mean(y - x); positive = y reads high vs x
      bias_high         -- mean bias where x > 10 µg/m³
      bias_low          -- mean bias where x ≤ 10 µg/m³
      n_high, n_low     -- sample counts for each bias regime
    """
    r    = np.corrcoef(x, y)[0, 1] if len(x) > 1 else np.nan
    rmse = np.sqrt(np.mean((x - y) ** 2)) if len(x) > 0 else np.nan
    overall_bias = np.mean(y - x) if len(x) > 0 else np.nan

    mask_high = x > 10
    mask_low  = x <= 10

    bias_high = np.mean(y[mask_high] - x[mask_high]) if np.sum(mask_high) > 0 else np.nan
    bias_low  = np.mean(y[mask_low]  - x[mask_low])  if np.sum(mask_low)  > 0 else np.nan

    slope, intercept = _slope_intercept(x[~is_outlier], y[~is_outlier])

    return {
        'slope':        slope,
        'intercept':    intercept,
        'r':            r,
        'rmse':         rmse,
        'overall_bias': overall_bias,
        'bias_high':    bias_high,
        'bias_low':     bias_low,
        'n_high':       int(np.sum(mask_high)),
        'n_low':        int(np.sum(mask_low)),
    }
