# Kathryn's AQI Sensor Comparison — 2025

Air quality sensor performance assessment comparing low-cost 3D-PAWS instruments against
regulatory-grade reference stations.

---

## Background

This project evaluates whether 3D-PAWS (3-Dimensional Printed Automatic Weather Station)
instruments can reliably track particulate matter (PM) concentrations compared to established
reference-grade sensors. We focus on **PM 1.0** and **PM 2.5** only — PM 10 readings from
3D-PAWS were determined to be unreliable and are excluded from analysis.

Two study sites were investigated:

### Study 1 — Erie / AJAX Site (Dec 2024 – May 2025)
Compares four instruments co-located (or nearby) at the AJAX reference station in Erie, CO:

| Instrument | Label in code | Notes |
|---|---|---|
| AJAX reference station | `AJAX Reference` | Regulatory-grade; the ground truth |
| 3D-PAWS Instrument 16 | `3D-PAWS_AQ_Testbed` | Co-located with AJAX; primary 3D-PAWS test unit |
| 3D-PAWS Instrument 18 | `Payne Observation Site` | Supervisor's personal weather station |
| 3D-PAWS Instrument 127 | `AQ Comparison AJAX` | Nearby; included for additional comparison |

### Study 2 — Boulder / Erie Community Center Site (Oct – Dec 2025)
Compares two 3D-PAWS instruments co-located with Colorado State Health (CU Boulder) sensor,
plus the Erie Community Center (ECC) reference station nearby:

| Instrument | Label in code | Notes |
|---|---|---|
| CU Boulder (Marine Street) | `CU Boulder Reference` | Primary reference for Study 2 |
| Erie Community Center | `Erie Community Center Reference` | Additional reference |
| 3D-PAWS Instrument 153 | `AQ_Comparison_2` | 1-minute sampling interval |
| 3D-PAWS Instrument 154 | `AQ_Comparison_1_5min` | 5-minute sampling interval; resolution comparison |

A wildfire event (Realization Fire) occurred on **Nov 19 2025, 02:00–06:00 UTC** and is of
special interest — set `FILTER_REALIZATION_FIRE = True` in `plotter.py` to zoom in on this event.

---

## Repository Structure

```
.
├── main.py          # Entry point — controls which steps to run
├── cleaner.py       # Step 1: standardizes raw CSV files from all sources
├── plotter.py       # Step 2: creates scatter plots with statistics
├── stats.py         # Step 3: calculates and saves summary statistics
├── analysis.py      # Shared helpers: stat computation, hourly resampling, study/label definitions
├── data/
│   ├── raw/         # Original CSV files from sensors and reference stations
│   │   ├── 3D-PAWS_Instrument-*.csv      — 3D-PAWS sensor data
│   │   ├── UplandS_1min_*.csv            — AJAX reference station
│   │   ├── Marine Street_*.csv           — CU Boulder reference station
│   │   ├── ECC_pm_*.csv                  — Erie Community Center (quarterly files)
│   │   └── daily_*.csv                   — EPA daily aggregates (not used)
│   └── reformatted/
│       └── cleaned/ # Output of cleaner.py; input to plotter.py and stats.py
├── plots/           # Output of plotter.py (scatter plots)
└── stats/
    └── test/        # Output of stats.py
```

---

## How to Run

### Prerequisites
- Python 3.9+
- `pandas`, `numpy`, `matplotlib`

### Running the pipeline

Open `main.py` and set flags in the `main()` call at the bottom:

```python
main(clean=True, plot=True, statistics=True)
```

- **`clean=True`** — reads `data/raw/`, writes standardized CSVs to `data/reformatted/cleaned/`
- **`plot=True`** — reads `data/reformatted/`, generates scatter plots and prints statistics
- **`statistics=True`** — reads `data/`, writes `pair_stats.csv` and `total_outliers.csv` to `stats/test/`

You can also run each module directly from the command line:

```bash
python cleaner.py data/raw data/reformatted 50.0
python plotter.py data/reformatted plots
python stats.py data stats/test
```

### Configuring which study to run

Each script (`plotter.py`, `stats.py`, `cleaner.py`) has a **CONFIG block** at the top of its
`main()` function. This is the only place you need to edit to change behavior — no
commenting or uncommenting required.

The most common setting to change is `STUDY`:

```python
STUDY = 1   # Erie / AJAX (Dec 2024 – May 2025)
STUDY = 2   # Boulder / ECC (Oct – Dec 2025)
```

This controls which instruments are included in all pairwise comparisons. Study instrument
definitions live in `analysis.py` (`STUDY_LABELS` and `FILE_LABEL_MAP`) — add new instruments
there if the study expands.

---

## Key Analysis Decisions

- **Outlier threshold: 50 µg/m³** — PM 2.5 readings above this are flagged as outliers and
  shown in red on scatter plots but are still included in the data (not removed). This threshold
  was chosen to separate typical urban background concentrations from smoke/event episodes.

- **Axis limit: 40 µg/m³** — scatter plots are capped at 40 on both axes to improve visibility
  of the bulk of data points; outliers outside this range are still plotted.

- **Hourly averages** — all scatter plots compare 1-hour averages (not minute-by-minute) to
  reduce noise. There is an optional point-for-point (minute-level) mode controlled by a flag
  in `plotter.py`.

- **Bias split at 10 µg/m³** — bias is reported separately for high (>10) and low (≤10)
  concentration regimes because sensor behavior often differs between clean-air and polluted
  conditions.

- **PM 10 excluded** — PM 10 from 3D-PAWS is dropped during cleaning; it was found to be
  unreliable. PM 1.0 is retained in some files but the primary comparison metric is PM 2.5.

---

## CONFIG Flags Reference

All behavior is controlled through CONFIG blocks.
Each script lists its own flags at the top of `main()` with descriptions.

### `cleaner.py`

| Flag | Default | What it does |
|---|---|---|
| `FILTER_OUTLIERS` | `False` | Replace PM 2.5 readings above `aqi_threshold` with NaN during cleaning and write a separate outlier CSV. When `False`, outliers are left in the data and flagged visually in `plotter.py` instead. |

### `plotter.py`

| Flag | Default | What it does |
|---|---|---|
| `STUDY` | `1` | Selects which instrument set to compare (1 = Erie/AJAX, 2 = Boulder/ECC) |
| `PM_COL` | `'PM 2.5'` | Which PM column to compare across instruments |
| `SAVE_PLOTS` | `True` | Save scatter plots to the output directory |
| `SAVE_BIAS_CSV` | `False` | Save the bias summary table to `output/bias_summary.csv` |
| `PLOT_WEEKLY_TIMESERIES` | `False` | Weekly hourly-average time series plots (useful for spotting data gaps) |
| `PLOT_DAILY_AVERAGES` | `False` | Daily-average time series plots, one line per instrument |
| `PLOT_POINT_FOR_POINT` | `False` | Minute-level scatter plots instead of hourly averages |
| `FILTER_REALIZATION_FIRE` | `False` | Restrict all data to the Nov 19 2025 wildfire event window (02:00–06:00 UTC) |

### `stats.py`

| Flag | Default | What it does |
|---|---|---|
| `STUDY` | `1` | Selects which instrument set to compute statistics for (should match `plotter.py`) |
| `PM_COL` | `'PM 2.5'` | Which PM column to compare across instruments |
