"""Some simple console message functions w/counting features for
errors, warnings, and info.  Also error exception raising and
tracebacks.

>>> from calcloud import log
>>> log.set_test_mode()
>>> log.reset()

>>> log.warning("this is a test warning.")
WARNING - this is a test warning.

>>> log.error("this is a test error.")
ERROR - this is a test error.

>>> log.error("this is another test error.")
ERROR - this is another test error.

>>> log.info("this is just informative.")
INFO - this is just informative.

>>> log.errors()
2

>>> log.status()
(2, 1, 1)

>>> log.standard_status()
INFO - 2 errors
INFO - 1 warnings
INFO - 1 infos

By default verbose messages are not emitted:

>>> log.verbose("this is a test verbose message.")

Calling set_verbose() turns on default verbosity=50:

>>> old_verbose = log.set_verbose()

>>> log.verbose("this is a test verbose message.")
DEBUG - this is a test verbose message.

No output is expected since default verbosity=50:

>>> log.verbose("this is a test suppressed verbose 60 message.", verbosity=60)

Output should now occur since verbosity=60:

>>> log.set_verbose(60)
50
>>> log.verbose("this is a test verbose 60 message.", verbosity=60)
DEBUG - this is a test verbose 60 message.

A number of context managers are defined for succinctly mapping nested
exceptions onto HSTDP messages or adding information:

>>> _ = log.set_verbose(old_verbose)
"""
import sys
import os
import logging
import pprint

DEFAULT_VERBOSITY_LEVEL = 50


class HstdpLogger:
    def __init__(self, name="HSTDP", enable_console=True, level=logging.DEBUG, enable_time=True):
        self.name = name

        self.handlers = []  # logging handlers, used e.g. to add console or file output streams
        self.filters = []  # simple HSTDP filters, used e.g. to mutate message text

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False
        self.formatter = self.set_formatter()
        self.console = None
        if enable_console:
            self.add_console_handler(level)

        # HSTDP internal counters of types of messages
        self.errors = 0
        self.warnings = 0
        self.infos = 0
        self.debugs = 0

        self.eol_pending = False

        # verbose_level handles HSTDP verbosity,  defaulting to 0 for no debug
        try:
            verbose_level = os.environ.get("CALCLOUD_VERBOSITY", 0)
            self.verbose_level = int(verbose_level)
        except Exception:
            warning(
                "Bad format for CALCLOUD_VERBOSITY =",
                repr(verbose_level),
                "Use e.g. -1 to squelch info, 0 for no debug,  50 for default debug output. 100 max debug.",
            )
            self.verbose_level = DEFAULT_VERBOSITY_LEVEL

    def set_formatter(self, enable_time=True, enable_msg_count=True):
        """Set the formatter attribute of `self` to a logging.Formatter and return it."""
        self.formatter = logging.Formatter(
            "{}%(levelname)s -%(message)s".format(
                "%(asctime)s - " if enable_time else "",
            )
        )
        for handler in self.handlers:
            handler.setFormatter(self.formatter)
        return self.formatter

    @property
    def msg_count(self):
        return "(%07d) -" % (self.infos + self.errors + self.warnings + self.debugs) if ADD_LOG_MSG_COUNT else ""

    def format(self, *args, **keys):
        end = keys.get("end", "\n")
        sep = keys.get("sep", " ")
        output = sep.join([str(arg) for arg in args]) + end
        for filter in self.filters:
            output = filter(output)
        return output

    def eformat(self, *args, **keys):
        keys["end"] = ""
        if self.eol_pending:
            self.write()
        return self.format(*args, **keys)

    def info(self, *args, **keys):
        self.infos += 1
        if self.verbose_level > -1:
            self.logger.info(self.eformat(self.msg_count, *args, **keys))

    def warn(self, *args, **keys):
        self.warnings += 1
        if self.verbose_level > -2:
            self.logger.warning(self.eformat(self.msg_count, *args, **keys))

    def error(self, *args, **keys):
        self.errors += 1
        if self.verbose_level > -3:
            self.logger.error(self.eformat(self.msg_count, *args, **keys))

    def debug(self, *args, **keys):
        self.debugs += 1
        self.logger.debug(self.eformat(self.msg_count, *args, **keys))

    def should_output(self, *args, **keys):
        verbosity = keys.get("verbosity", DEFAULT_VERBOSITY_LEVEL)
        return not self.verbose_level < verbosity

    def verbose(self, *args, **keys):
        if self.should_output(*args, **keys):
            self.debug(*args, **keys)

    def verbose_warning(self, *args, **keys):
        if self.should_output(*args, **keys):
            self.warn(*args, **keys)

    def write(self, *args, **keys):
        """Output a message to stdout, formatting each positional parameter
        as a string.
        """
        output = self.format(*args, **keys)
        self.eol_pending = not output.endswith("\n")
        sys.stderr.flush()
        sys.stdout.write(output)
        sys.stdout.flush()

    def status(self):
        return self.errors, self.warnings, self.infos

    def reset(self):
        self.errors = self.warnings = self.infos = self.debugs = 0

    def set_verbose(self, level=True):
        assert -3 <= level <= 100, "verbosity level must be in range -3..100"
        old_verbose = self.verbose_level
        if level is True:
            level = DEFAULT_VERBOSITY_LEVEL
        elif not level:
            level = 0
        self.verbose_level = level
        return old_verbose

    def get_verbose(self):
        return self.verbose_level

    def add_console_handler(self, level=logging.DEBUG, stream=sys.stderr):
        if self.console is None:
            self.console = self.add_stream_handler(stream)

    def remove_console_handler(self):
        if self.console is not None:
            self.remove_stream_handler(self.console)
            self.console = None

    def add_stream_handler(self, filelike, level=logging.DEBUG):
        handler = logging.StreamHandler(filelike)
        handler.setLevel(level)
        handler.propagate = False
        handler.setFormatter(self.formatter)
        self.handlers.append(handler)
        self.logger.addHandler(handler)
        return handler

    def remove_stream_handler(self, handler):
        self.handlers.remove(handler)
        self.logger.removeHandler(handler)

    def fatal_error(self, *args, **keys):
        error("(FATAL)", *args, **keys)
        sys.exit(-1)  # FATAL == totally unambiguous


THE_LOGGER = HstdpLogger("HSTDP")

info = THE_LOGGER.info
error = THE_LOGGER.error
warning = THE_LOGGER.warn
verbose_warning = THE_LOGGER.verbose_warning
verbose = THE_LOGGER.verbose
should_output = THE_LOGGER.should_output
debug = THE_LOGGER.debug
fatal_error = THE_LOGGER.fatal_error
status = THE_LOGGER.status
reset = THE_LOGGER.reset
write = THE_LOGGER.write
set_verbose = THE_LOGGER.set_verbose
get_verbose = THE_LOGGER.get_verbose
add_console_handler = THE_LOGGER.add_console_handler
remove_console_handler = THE_LOGGER.remove_console_handler
add_stream_handler = THE_LOGGER.add_stream_handler
remove_stream_handler = THE_LOGGER.remove_stream_handler

format = THE_LOGGER.format


def increment_errors(N=1):
    """Increment the error count by N without issuing a log message."""
    THE_LOGGER.errors += N


def errors():
    """Return the global count of errors."""
    return THE_LOGGER.errors


def warnings():
    """Return the global count of errors."""
    return THE_LOGGER.warnings


def infos():
    """Return the global count of infos."""
    return THE_LOGGER.infos


def set_test_mode():
    """Route log messages to standard output for testing with doctest."""
    remove_console_handler()
    add_console_handler(stream=sys.stdout)
    set_log_time(False)


def set_log_time(enable_time=False):
    """Set the flag for including time in log messages.  Ignore HSTDP_LOG_TIME."""
    THE_LOGGER.set_formatter(enable_time)


# ===========================================================================

ADD_LOG_MSG_COUNT = False


def set_add_log_msg_count(flag):
    global ADD_LOG_MSG_COUNT
    old_flag = ADD_LOG_MSG_COUNT
    ADD_LOG_MSG_COUNT = flag
    return old_flag


def get_add_log_msg_count():
    return ADD_LOG_MSG_COUNT


# ===========================================================================


class PP:
    """A wrapper to defer pretty printing until after it's known a verbose
    message will definitely be output.
    """

    def __init__(self, ppobj):
        self.ppobj = ppobj

    def __str__(self):
        return pprint.pformat(self.ppobj)


class Deferred:
    """A wrapper to delay calling a callable until after it's known a verbose
    message will definitely be output.
    """

    def __init__(self, ppobj):
        self.ppobj = ppobj

    def __str__(self):
        return str(self.ppobj())


# ===========================================================================


def standard_status():
    """Print out errors, warnings, and infos."""
    errors, warnings, infos = THE_LOGGER.status()
    info(errors, "errors")
    info(warnings, "warnings")
    info(infos, "infos")


# ==============================================================================


def srepr(obj):
    """Return the repr() of the str() of obj"""
    return repr(str(obj))


# ==============================================================================


def divider(name="", char="-", n=75, func=info, **keys):
    """Create a log divider line consisting of `char` repeated `n` times
    possibly with `name` injected into the center of the divider.
    Output it as a string to logging function `func` defaulting to info().
    """
    if name:
        n2 = (n - len(name) - 2) // 2
        func(char * n2, name, char * n2, **keys)
    else:
        func(char * n, **keys)


# ===================================================================


def test():
    from calcloud import log
    import doctest

    return doctest.testmod(log)


if __name__ == "__main__":
    print(test())
