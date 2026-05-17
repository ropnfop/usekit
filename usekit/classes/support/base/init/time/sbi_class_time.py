# Path: usekit.classes.support.base.init.time.sbi_class_time.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# -----------------------------------------------------------------------------------------------

from datetime import datetime, timedelta
import time


class TimeHandler:
    """
    Practical time utilities for USEKIT
    Optimized for real mobile coding scenarios
    Default: Always returns local time
    """
    
    # ============================================
    # CORE: Most frequently used
    # ============================================
    
    def now(self):
        """
        Get current local time
        
        Returns:
            datetime: Current local datetime
            
        Example:
            >>> t.now()
            datetime(2025, 12, 25, 14, 30, 22)
        """
        return datetime.now()
    
    def str(self, dt=None, fmt='%Y-%m-%d %H:%M:%S'):
        """
        Convert datetime to string
        
        Args:
            dt: datetime object (None = now)
            fmt: format string
            
        Returns:
            str: Formatted time string
            
        Example:
            >>> t.str()
            '2025-12-25 14:30:22'
            >>> t.str(fmt='%Y%m%d')
            '20251225'
        """
        if dt is None:
            dt = self.now()
        return dt.strftime(fmt)
    
    def file(self, dt=None):
        """
        Filename-safe timestamp
        
        Args:
            dt: datetime object (None = now)
            
        Returns:
            str: Format like '2025-12-25_143022'
            
        Example:
            >>> filename = f"backup_{t.file()}.json"
            'backup_2025-12-25_143022.json'
        """
        return self.str(dt, '%Y-%m-%d_%H%M%S')
    
    # ============================================
    # DIFF: Time difference calculation (CRITICAL)
    # ============================================
    
    def diff(self, dt1, dt2=None, unit='seconds'):
        """
        Calculate time difference
        
        Args:
            dt1: first datetime
            dt2: second datetime (None = now)
            unit: 'seconds', 'minutes', 'hours', 'days'
            
        Returns:
            float: Time difference in specified unit
            
        Example:
            >>> last_time = t.now()
            >>> # ... do something ...
            >>> diff_seconds = t.diff(last_time)
            >>> # or
            >>> diff_seconds = t.diff(t.now(), last_time)
        """
        if dt2 is None:
            dt2 = self.now()
        
        delta = dt2 - dt1
        seconds = delta.total_seconds()
        
        if unit == 'seconds':
            return seconds
        elif unit == 'minutes':
            return seconds / 60
        elif unit == 'hours':
            return seconds / 3600
        elif unit == 'days':
            return seconds / 86400
        else:
            return seconds
    
    def elapsed(self, start_dt):
        """
        Get seconds elapsed since start_dt
        More intuitive than diff for timing operations
        
        Args:
            start_dt: start datetime
            
        Returns:
            float: Seconds elapsed
            
        Example:
            >>> start = t.now()
            >>> # ... do something ...
            >>> seconds = t.elapsed(start)
        """
        return self.diff(start_dt, self.now(), 'seconds')
    
    # ============================================
    # CONVERT: Type conversions
    # ============================================
    
    def stamp(self, dt=None):
        """
        Get unix timestamp
        
        Args:
            dt: datetime object (None = now)
            
        Returns:
            int: Unix timestamp
            
        Example:
            >>> t.stamp()
            1735108222
        """
        if dt is None:
            return int(time.time())
        return int(dt.timestamp())
    
    def parse(self, s, fmt='%Y-%m-%d %H:%M:%S'):
        """
        Parse string to datetime
        
        Args:
            s: time string
            fmt: format string
            
        Returns:
            datetime: Parsed datetime
            
        Example:
            >>> t.parse('2025-12-25 14:30:22')
            datetime(2025, 12, 25, 14, 30, 22)
        """
        return datetime.strptime(s, fmt)
    
    def from_stamp(self, ts):
        """
        Convert timestamp to datetime
        
        Args:
            ts: unix timestamp
            
        Returns:
            datetime: Local datetime
            
        Example:
            >>> t.from_stamp(1735108222)
            datetime(2025, 12, 25, 14, 30, 22)
        """
        return datetime.fromtimestamp(ts)
    
    # ============================================
    # FORMAT: Common format shortcuts
    # ============================================
    
    def tag(self, dt=None):
        """
        Compact timestamp format
        
        Args:
            dt: datetime object (None = now)
            
        Returns:
            str: Format like '20251225_143022'
            
        Example:
            >>> t.tag()
            '20251225_143022'
        """
        return self.str(dt, '%Y%m%d_%H%M%S')
    
    def log(self, dt=None):
        """
        Log prefix format
        
        Args:
            dt: datetime object (None = now)
            
        Returns:
            str: Format like '[2025-12-25 14:30:22]'
            
        Example:
            >>> print(f"{t.log()} Process started")
            [2025-12-25 14:30:22] Process started
        """
        return f"[{self.str(dt)}]"
    
    def iso(self, dt=None):
        """
        ISO 8601 format
        
        Args:
            dt: datetime object (None = now)
            
        Returns:
            str: ISO 8601 formatted string
            
        Example:
            >>> t.iso()
            '2025-12-25T14:30:22.123456'
        """
        if dt is None:
            dt = self.now()
        return dt.isoformat()
    
    def date(self, dt=None):
        """
        Date only format
        
        Args:
            dt: datetime object (None = now)
            
        Returns:
            str: Format like '2025-12-25'
            
        Example:
            >>> t.date()
            '2025-12-25'
        """
        return self.str(dt, '%Y-%m-%d')
    
    def time_only(self, dt=None):
        """
        Time only format
        
        Args:
            dt: datetime object (None = now)
            
        Returns:
            str: Format like '14:30:22'
            
        Example:
            >>> t.time_only()
            '14:30:22'
        """
        return self.str(dt, '%H:%M:%S')
    
    # ============================================
    # CALCULATE: Time arithmetic
    # ============================================
    
    def add(self, dt=None, days=0, hours=0, minutes=0, seconds=0):
        """
        Add time duration
        
        Args:
            dt: datetime object (None = now)
            days: days to add
            hours: hours to add
            minutes: minutes to add
            seconds: seconds to add
            
        Returns:
            datetime: New datetime with duration added
            
        Example:
            >>> future = t.add(days=1, hours=2)
            >>> future = t.add(some_dt, minutes=30)
        """
        if dt is None:
            dt = self.now()
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return dt + delta
    
    def sub(self, dt=None, days=0, hours=0, minutes=0, seconds=0):
        """
        Subtract time duration
        
        Args:
            dt: datetime object (None = now)
            days: days to subtract
            hours: hours to subtract
            minutes: minutes to subtract
            seconds: seconds to subtract
            
        Returns:
            datetime: New datetime with duration subtracted
            
        Example:
            >>> past = t.sub(days=1, hours=2)
            >>> past = t.sub(some_dt, minutes=30)
        """
        if dt is None:
            dt = self.now()
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return dt - delta
    
    def ago(self, days=0, hours=0, minutes=0, seconds=0):
        """
        Get time in the past
        Shortcut for sub() with more intuitive name
        
        Args:
            days: days ago
            hours: hours ago
            minutes: minutes ago
            seconds: seconds ago
            
        Returns:
            datetime: Past datetime
            
        Example:
            >>> yesterday = t.ago(days=1)
            >>> two_hours_ago = t.ago(hours=2)
        """
        return self.sub(days=days, hours=hours, minutes=minutes, seconds=seconds)
    
    def after(self, days=0, hours=0, minutes=0, seconds=0):
        """
        Get time in the future
        Shortcut for add() with more intuitive name
        
        Args:
            days: days after
            hours: hours after
            minutes: minutes after
            seconds: seconds after
            
        Returns:
            datetime: Future datetime
            
        Example:
            >>> tomorrow = t.after(days=1)
            >>> in_two_hours = t.after(hours=2)
        """
        return self.add(days=days, hours=hours, minutes=minutes, seconds=seconds)
"""
)
create_file(
    description="Create time module __init__.py with ut singleton",
    path="/home/claude/usekit/classes/support/base/time/__init__.py",
    file_text="""from .handler import TimeHandler

# Create singleton instance
ut = TimeHandler()

__all__ = ['ut', 'TimeHandler']