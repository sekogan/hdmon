from typing import Dict
import subprocess

from .logger import LOGGER as logger


_TIMEOUT: float = 5 * 60  # 5 minutes


def run(command: str, env: Dict[str, str], timeout=_TIMEOUT):
    logger.info(
        'Running "%s" where %s',
        command,
        ", ".join("${}={}".format(key, value) for key, value in env.items()),
    )
    try:
        subprocess.run(
            command,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=True,
        )
    except subprocess.TimeoutExpired as error:
        logger.error(
            'Timeout while running command "%s", command output:\n%s',
            command,
            error.stdout,
        )
    except subprocess.CalledProcessError as error:
        logger.error(
            'Command "%s" failed with exit code %d, command output:\n%s',
            command,
            error.returncode,
            error.stdout,
        )
