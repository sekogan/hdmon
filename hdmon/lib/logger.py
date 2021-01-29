import logging
import os
import sys


LOGGER = logging.getLogger()


_DEBUG = bool(os.environ.get("DEBUG", False))


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if _DEBUG else logging.INFO,
    format="%(message)s",
)
