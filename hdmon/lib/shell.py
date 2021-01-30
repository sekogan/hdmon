from typing import Dict
import subprocess

from .error_handling import Error


_TIMEOUT: float = 5 * 60  # 5 minutes


class ShellError(Error):
    def __init__(self, command_output):
        self.command_output = command_output


class TimeoutError(ShellError):
    pass


class ExitCodeError(ShellError):
    def __init__(self, exit_code, command_output):
        super(ExitCodeError, self).__init__(command_output)
        self.exit_code = exit_code


def run(command: str, env: Dict[str, str], timeout=_TIMEOUT):
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
        raise TimeoutError(error.stdout)
    except subprocess.CalledProcessError as error:
        raise ExitCodeError(error.returncode, error.stdout)
