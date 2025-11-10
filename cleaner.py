import numpy as np
import pandas as pd
from pathlib import Path

data = Path("/Users/rzieber/Documents/3D-PAWS/AQI_Comparison/report")
#output = Path("/Users/rzieber/Documents/3D-PAWS/AQI_Comparison/data_cleaned")
output = Path("/Users/rzieber/Documents/3D-PAWS/AQI_Comparison/data_cleaned")

dataframes = []
names = []

outliers = pd.DataFrame()

variable_mapper = { # 3D-PAWS : AJAX co-located site
    'pm1s10':'PM 1.0',
    'pm1s25':'PM 2.5',
    'pm1e10':'PM 1.0',
    'pm1e25':'PM 2.5'
}

aqi_threshold = 50  # µg/m³

for csv in data.rglob("*.csv"):
    name = str(csv.stem)
    df = None

    is_ajax = False
    if name.startswith("UplandS") and name.endswith("_cleaned"):
        print(name)
        df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])
        is_ajax = True

    elif name.endswith("_cleaned"):
        print(name)
        df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])
    
    else: continue

    for var_3dpaws, var_ajax in variable_mapper.items():
        col = var_ajax if is_ajax else var_3dpaws
        if col not in df.columns:
            continue

        df[col] = pd.to_numeric(df[col], errors='coerce')

        mask = df[col] > aqi_threshold
        if mask.any():
            outliers = pd.concat([outliers, df.loc[mask, ['time', col]]], axis=0)

        df.loc[df[col] > aqi_threshold, col] = np.nan

    df.to_csv(output / f"{name}.csv", index=False)       

    if not outliers.empty:
        outliers.to_csv(output / f"{name}_outliers.csv", index=False) 
