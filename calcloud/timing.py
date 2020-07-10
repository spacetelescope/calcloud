"""This module provides functions and classes used to track and compute
rate metrics.
"""
from collections import Counter
import datetime
import os

from calcloud import log

# ===================================================================

class TimingStats:
    """Track and compute counts and counts per second."""
    def __init__(self, output=None):
        self.counts = Counter()
        self.started = None
        self.stopped = None
        self.elapsed = None
        self.output = log.info if output is None else output
        self.start()

    def get_stat(self, name):
        """Return the value of statistic `name`."""
        return self.counts[name]

    def increment(self, name, amount=1):
        """Add `amount` to stat count for `name`."""
        self.counts[name] += amount

    def start(self):
        """Start the timing interval."""
        self.started = datetime.datetime.now()
        return self

    def stop(self):
        """Stop the timing interval."""
        self.stopped = datetime.datetime.now()
        self.elapsed = self.stopped - self.started

    def report(self):
        """Output all stats."""
        self.stop()
        self.msg("STARTED", str(self.started)[:-4])
        self.msg("STOPPED", str(self.stopped)[:-4])
        self.msg("ELAPSED", str(self.elapsed)[:-4])
        self.report_stats()

    def report_stats(self):
        """Output a stat for each kind defined."""
        for kind in self.counts:
            self.report_stat(kind)

    def report_stat(self, name):
        """Output stats on `name`."""
        count, rate = self.status(name)
        self.msg(count, "at", rate)

    def raw_status(self, name):
        self.stop()
        counts = self.counts[name]
        rate = self.counts[name] / self.elapsed.total_seconds()
        return counts, rate

    def status(self, name):
        """Return human readable (count, rate) for `name`."""
        counts, rate = self.raw_status(name)
        count_str = human_format_number(counts) + " " + name
        rate_str = human_format_number(rate) + " " + name + "-per-second"
        return count_str, rate_str

    def log_status(self, name, intro, total=None):
        """Do log output about stat `name` using `intro` as the descriptive lead-in to
        the stats.
        """
        stat, stat_per_sec = self.raw_status(name)
        if total is not None:
            self.msg(intro, "[",
                     human_format_number(stat), "/",
                     human_format_number(total), name, "]",
                     "[",
                     human_format_number(stat_per_sec), name + "-per-second ]")
        else:
            self.msg(intro,
                     "[", human_format_number(stat), name, "]",
                     "[", human_format_number(stat_per_sec), name + "-per-second ]")

    def msg(self, *args):
        """Format (*args, **keys) using log.format() and call output()."""
        self.output(*args, eol="")

# ===================================================================

def total_size(filepaths):
    """Return the total size of all files in `filepaths` as an integer."""
    return sum([os.stat(filename).st_size for filename in filepaths])

# ===================================================================

def file_size(filepath):
    """Return the size of `filepath` as an integer."""
    return os.stat(filepath).st_size

# ===================================================================

def elapsed_time(func):
    """Decorator to report on elapsed time for a function call."""
    def elapsed_wrapper(*args, **keys):
        stats = TimingStats()
        stats.start()
        result = func(*args, **keys)
        stats.stop()
        stats.msg("Timing for", repr(func.__name__))
        stats.report()
        return result
    elapsed_wrapper.__name__ = func.__name__ + "[elapsed_time]"
    elapsed_wrapper.__doc__ = func.__doc__
    return elapsed_wrapper

# ===================================================================

def human_format_number(number):
    """Reformat `number` by switching to engineering units and dropping to two fractional digits,
    10s of megs for G-scale files.
    """
    convert = [
        (1e12, "T"),
        (1e9 , "G"),
        (1e6 , "M"),
        (1e3 , "K"),
        ]
    for limit, sym in convert:
        if isinstance(number, (float, int)) and number > limit:
            number /= limit
            break
    else:
        sym = ""
    if isinstance(number, int):
        # numstr = "%d" % number
        numstr = "{}".format(number)
    else:
        numstr = "{:0.1f} {}".format(number, sym)
    return "{!s:>7}".format(numstr)
