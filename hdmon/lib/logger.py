import logging
import os
import sys


LOGGER = logging.getLogger()


_DEBUG = bool(os.environ.get("DEBUG", False))


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if _DEBUG else logging.INFO,
    format="%(levelname)s: %(message)s",
)


def log_current_exception():
    _cls, error, traceback = sys.exc_info()
    if _DEBUG:
        LOGGER.error("%s", traceback.format_exc())
    else:
        LOGGER.error("%s", str(error))
