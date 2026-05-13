import cleaner
import plotter
import stats

def main(clean:bool=False, plot:bool=False, statistics:bool=False):
    """
    -----------------------------------------------------------------------------------------
    Entry point for Kathryn's 2025 AQI sensor comparison.

    Set flags here to control which steps run:
        clean      — standardize raw CSVs into a common format (cleaner.py)
        plot       — generate scatter plots and print statistics (plotter.py)
        statistics — count outliers and write summary CSV (stats.py)

    Adjust file paths below as needed for your local setup.
    -----------------------------------------------------------------------------------------
    """
    if clean:
        # aqi_threshold: PM 2.5 values above this (µg/m³) are flagged as outliers.
        # 50.0 was chosen to separate typical urban background from smoke/event episodes.
        # See cleaner.py to control outlier filtering
        cleaner.main("data/raw", "data/reformatted", 50.0)

    if plot:
        # See plotter.py to control which plots get generated
        plotter.main("data/reformatted", "plots")

    if statistics:
        stats.main("data", "stats/test")

if __name__ == '__main__':
    main(
        clean=False,
        plot=True,
        statistics=False
    )
