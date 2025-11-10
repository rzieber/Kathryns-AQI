import warnings
import pandas as pd
import numpy as np
from pathlib import Path
import sensortoolkit as stk
from sensortoolkit import *

"""
========================================================================
Dataframe creation.
========================================================================
"""
data = Path("/Users/rzieber/Documents/3D-PAWS/AQI_Comparison/data_cleaned")
output = Path("/Users/rzieber/Documents/3D-PAWS/AQI_Comparison/stats")

dataframes = []
names = ['Payne Obs. Site', 'AJAX Reference', 'AQI Testbed', 'AJAX Co-Located']

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)

    for csv in data.rglob("*.csv"):
        print(str(csv.name))
        df = pd.read_csv(csv, low_memory=False, parse_dates=['time'])
        df['week'] = df['time'].dt.to_period('W')
        df.set_index('time')
        dataframes.append(df)

print()

variable_mapper = { # 3D-PAWS : AJAX co-located site
    'pm1s10':'PM 1.0',
    'pm1s25':'PM 2.5',
    'pm1e10':'PM 1.0',
    'pm1e25':'PM 2.5'
}

# create statistical summary of the data
# stats we care about: corr. coeff., rmse, std, 
