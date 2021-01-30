import logging
import os
import sys
import traceback


LOGGER = logging.getLogger()


_DEBUG = bool(os.environ.get("DEBUG", False))


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if _DEBUG else logging.INFO,
    format="%(levelname)s: %(message)s",
)


def log_current_exception():
    if _DEBUG:
        LOGGER.error("%s", traceback.format_exc())
    else:
        _cls, error, _traceback = sys.exc_info()
        LOGGER.error("%s", str(error))
