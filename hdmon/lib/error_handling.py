import functools

from .logger import LOGGER as logger


class Error(Exception):
    pass


class ConfigurationError(Error):
    pass


class UsageError(Error):
    pass


def no_exceptions(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            logger.error("%s", str(error))

    return wrapper
