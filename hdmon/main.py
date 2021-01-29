#!/usr/bin/env python3

"""
Disk monitoring and power management service
"""


from typing import Iterator, List
import argparse
import os
import yaml

from .lib import shell
from .lib.disk_activity_monitor import DiskActivityMonitor
from .lib.disk_spin_down_controller import DiskSpinDownController
from .lib.disk_spin_down_strategy import create as create_spin_down_strategy
from .lib.error_handling import Error, ConfigurationError, UsageError
from .lib.logger import LOGGER as logger
from .lib.scheduler import Scheduler


CONFIG_LOCATIONS = [
    "/etc/hdmon.yml",
]


def parse_args():
    parser = argparse.ArgumentParser(__doc__)

    parser.add_argument("-c", "--config", default=None, help="configuration file path")

    return parser.parse_args()


def load_config(path):
    with open(path) as fh:
        return yaml.safe_load(fh)


class DiskMonitorService:
    def __init__(self, config):
        self._scheduler = Scheduler()
        self._monitor = DiskActivityMonitor(scheduler=self._scheduler)

        profiles = config.get("profiles", [])
        if not profiles:
            logger.warning("No profiles in configuration file, nothing to do")

        for index, profile in enumerate(profiles):
            disk_paths = list(self._find_disk_paths(profile["disks"] or []))
            if not disk_paths:
                logger.warning("No disks in profile %d, nothing to do", index + 1)

            spin_down_config = profile.get("spin_down")
            if spin_down_config is not None:
                self._create_spin_down_controllers(disk_paths, spin_down_config)

    def run(self):
        logger.info("Running...")
        self._scheduler.run()

    def _create_spin_down_controllers(self, disk_paths, spin_down_config):
        strategy_name = spin_down_config["when"]
        strategy_options = spin_down_config.get("options", {})
        for disk_path in disk_paths:
            controller = DiskSpinDownController(
                disk_path=disk_path,
                spin_down_strategy=create_spin_down_strategy(
                    strategy_name=strategy_name,
                    options=strategy_options,
                ),
                spin_down_actuator=lambda disk_path=disk_path: self._run_shell_command(
                    command=spin_down_config["command"],
                    env={"disk_path": disk_path},
                ),
                scheduler=self._scheduler,
            )
            self._monitor.add_observer(disk_path, controller)
            logger.info(
                "Disk %s will be spun down when %s (%s)",
                disk_path,
                strategy_name,
                ", ".join(
                    "{}={}".format(key, value)
                    for key, value in strategy_options.items()
                )
                if strategy_options
                else "-",
            )

    @staticmethod
    def _find_disk_paths(patterns: List[str]) -> Iterator[str]:
        from .lib import filesystem

        for pattern in patterns:
            for path in filesystem.find(pattern):
                if path.is_dir():
                    continue
                if str(path.parent) != "/dev":
                    raise ConfigurationError(f'Device file "{path}" is outside /dev')
                yield str(path)

    @staticmethod
    def _run_shell_command(command, env):
        logger.info(
            'Running "%s" where %s',
            command,
            ", ".join("${}={}".format(key, value) for key, value in env.items()),
        )
        try:
            shell.run(command, env)
        except shell.TimeoutError as error:
            logger.error(
                'Timeout while running command "%s", command output:\n%s',
                command,
                error.command_output,
            )
        except shell.ExitCodeError as error:
            logger.error(
                'Command "%s" failed with exit code %d, command output:\n%s',
                command,
                error.exit_code,
                error.command_output,
            )


def main():
    try:
        args = parse_args()

        config_path = args.config
        if config_path is not None:
            if not os.path.isfile(config_path):
                raise UsageError(f'Cannot find configuration file "{config_path}"')
        else:
            for location in CONFIG_LOCATIONS:
                if os.path.isfile(location):
                    config_path = location
                    break

            if config_path is None:
                locations = ", ".join(
                    '"{}"'.format(location) for location in CONFIG_LOCATIONS
                )
                raise ConfigurationError(
                    f"Cannot find configuration file in known locations: {locations}"
                )
        config = load_config(config_path)

        DiskMonitorService(config).run()
        return 0
    except Error as error:
        logger.error("%s", error)
        return 1


if __name__ == "__main__":
    exit(main())
