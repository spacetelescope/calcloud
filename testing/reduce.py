import sys
import os, os.path
import re
import glob
import pysh
import subprocess
from collections import defaultdict
import pprint

# ----------------------------------------------------------------------------------------------------

def _sh(command, **keys):
    """Run a subprogram,  inheriting stdout and stderr from the calller, and
    return the program exit status.  Output is not captured.
    If raise_on_error is True,  raise an exception on non-zero program exit.
    """
    if len(command) == 1:
        lines = command[0].splitlines()
        command = (" && ".join(
            [line.strip() for line in lines
             if line.strip()]
        ),)
    baseline = dict(
        env=os.environ,
        universal_newlines=True,
        shell=True)
    keys = dict(keys)
    keys.update(baseline)
    return subprocess.run(command, **keys)

def out(*command, **keys):
    """Run a subprogram and return it's stdout."""
    keys = dict(keys)
    keys["stdout"] = subprocess.PIPE
    return _sh(command, **keys).stdout

def lines(*command, **keys):
    return out(*command, **keys).splitlines()

# ----------------------------------------------------------------------------------------------------

class BatchLogReducer:
    def __init__(self, logdir):
        self.dir = logdir
        self.failures = defaultdict(int)
        self.category = "none"
        self.total_failures = 0

    def divider(self):
        print("+-"*60)
        print(".", file=sys.stderr, end="")
        sys.stderr.flush()

    def get_process_files(self):
        return lines(f"find {self.dir} -name process.txt")

    start_pattern = r"Started processing"
    failure_patterns = [
        r"Exception",
        r"Traceback",
        r"exited with error status",
        r"ERROR",
    ]
    suppress = [
        # "runastrodriz",
    ]
    categories = [
        r"Retrieving data",
        r"Computing bestrefs",
        r"runastrodriz",
        r"Running: \('cal",
        r"Saving outputs",
    ]
    completions = [
        r"complete. >>>>>>>>",
        r"Download data complete.",
        r"Bestrefs complete",
    ]

    def reduce(self):
        for file in self.get_process_files():
            with open(file) as text:
                all_text = text.read()
                self.category = "none"
                self.reduce_one_job(all_text)
        self.divider()
        print("Total failures:", self.total_failures)
        print("Categories:", pprint.pformat(dict(self.failures)))

    def reduce_one_job(self, all_text):
        fail_output = self.reduce_lines(all_text.splitlines())
        self.divider()
        if not fail_output: # no fail output == no failure
            # Print 2nd line of job, IPPPSSOOT + cmd
            print(all_text.splitlines()[1])
        elif self.category in self.suppress:
            print("+-"*20, "XXXX", self.category,  "FAILED/SUPPRESSED XXXX", "+-"*20)
        else:
            print("+-"*20, "XXXX", self.category,  "FAILED XXXX", "+-"*20)
            print(fail_output)
            self.divider()
            print(all_text)
        self.divider()

    def reduce_lines(self, lines):
        for (i, line) in enumerate(lines):
            for pattern in self.failure_patterns:
                if re.search(pattern, line):
                    self.failures[(self.category, pattern)] += 1
                    self.total_failures += 1
                    return f"Failed on line {i}\n{line}"
            for category in self.categories:
                if re.search(category, line):
                    self.category = category
        return ""

def main(logdir):
    reducer = BatchLogReducer(logdir)
    return reducer.reduce()

if __name__ == "__main__":
    main(sys.argv[1])
