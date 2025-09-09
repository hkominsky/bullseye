class ProgressTracker:
    """
    Tracks the progress of a process using print statements.
    """
    
    def __init__(self, total_steps: int = None):
        """
        Initialize the ProgressTracker.
        If total_steps is None, percentages won't be shown.
        """
        self.total_steps = total_steps
        self.current_step = 0

    def start(self, ticker: str):
        """
        Print start of processing.
        """
        print(f"Processing started for {ticker}")

    def step(self, message: str):
        """
        Print completion of processing step, calculates what percentage of the total steps have been completed.
        """
        self.current_step += 1
        if self.total_steps:
            percent = (self.current_step / self.total_steps) * 100
            print(f"[{percent:.0f}%] {message}")
        else:
            print(f"[{self.current_step}] {message}")

    def complete(self, ticker: str):
        """
        Print completion of processing.
        """
        print(f"{ticker} market brief complete")