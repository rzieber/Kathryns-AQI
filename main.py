import cleaner
import plotter
import stats

def main(clean:bool=False, plot:bool=False, statistics:bool=False):
    """
    -----------------------------------------------------------------------------------------
    Workflow for Kathryn's 2025 AQI sensor comparison. Adjust file paths in function calls
    as necessary. Set parameters in main method call.
    0. Set up folder struct 
    1. Clean the data           cleaner.py 
    2. Run the plotter          plotter.py
    3. Calculate AQI stats      stats.py *uses EPA's analysis library sensortoolkit
    -----------------------------------------------------------------------------------------
    """
    if clean:       cleaner.main("data/raw", "data/reformatted", 50.0)
    if plot:        plotter.main("data/reformatted", "/path/to/local/storage")
    if statistics:  stats.main("data", "stats/test")

if __name__ == '__main__':
    main(plot=True)
