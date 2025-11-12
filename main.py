import cleaner
import plotter
import stats

def main():
    """
    -----------------------------------------------------------------------------------------
    Workflow for Kathryn's 2025 AQI sensor comparison.
    1. Clean the data           cleaner.py
    2. Run the plotter          plotter.py
    3. Calculate AQI stats      stats.py *uses EPA's analysis library sensortoolkit
    -----------------------------------------------------------------------------------------
    """
    cleaner.main("data\\raw", "data\\cleaned", 50)
    # plotter.main("data\\cleaned\\test", "plots\\cleaned\\test")
    # stats.main("data\\cleaned", "report\\test")

if __name__ == '__main__':
    main()
