import functools

from .logger import log_current_exception


class Error(Exception):
    pass


class ConfigurationError(Error):
    pass


class UsageError(Error):
    pass


def log_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            log_current_exception()

    return wrapper
