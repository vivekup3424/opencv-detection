"""Date and time utility functions."""

from datetime import datetime, timezone
from typing import Optional
import time


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def timestamp_to_datetime(timestamp: float) -> datetime:
    """Convert Unix timestamp to UTC datetime."""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def datetime_to_timestamp(dt: datetime) -> float:
    """Convert datetime to Unix timestamp."""
    return dt.timestamp()


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime as string."""
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse datetime string."""
    return datetime.strptime(date_str, format_str).replace(tzinfo=timezone.utc)


def sleep_ms(milliseconds: int) -> None:
    """Sleep for specified milliseconds."""
    time.sleep(milliseconds / 1000.0)


def get_elapsed_ms(start_time: float) -> float:
    """Get elapsed milliseconds since start_time."""
    return (time.time() - start_time) * 1000.0


class Timer:
    """Simple timer utility for measuring execution time."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self) -> float:
        """Stop the timer and return elapsed time in seconds."""
        if self.start_time is None:
            raise ValueError("Timer not started")
        
        self.end_time = time.time()
        return self.elapsed_seconds()
    
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            raise ValueError("Timer not started")
        
        end = self.end_time or time.time()
        return end - self.start_time
    
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed_seconds() * 1000.0
