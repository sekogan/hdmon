#!/usr/bin/env python3

"""
Disk monitoring and power management service
"""


from dataclasses import dataclass
from typing import Iterator, List, Iterable, Any, Dict, Generator
import argparse
import os
import yaml

from .lib import shell
from .lib.disk_activity_monitor import DiskActivityMonitor
from .lib.disk_presence_monitor import DiskPresenceMonitor, DiskPresenceObserver
from .lib.disk_spin_down_controller import DiskSpinDownController
from .lib.disk_spin_down_strategy import create as create_spin_down_strategy
from .lib.disk_stats_monitor import DiskStatsMonitor
from .lib.error_handling import Error, ConfigurationError, UsageError, log_exceptions
from .lib.logger import LOGGER as logger, log_current_exception
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


@dataclass
class _MonitoredDisk:
    device_name: str  # sda
    disk_path: str  # /dev/sda
    profile_id: int
    profile: Dict[str, Any]


class DiskMonitoringService(DiskPresenceObserver):
    def __init__(self, config):
        logger.debug("Debug mode is ON")

        self._scheduler = Scheduler()

        self._disk_stats_monitor = DiskStatsMonitor(scheduler=self._scheduler)
        self._disk_presence_monitor = DiskPresenceMonitor()
        self._disk_activity_monitor = DiskActivityMonitor()

        self._disk_stats_monitor.add_observer(self._disk_presence_monitor)
        self._disk_stats_monitor.add_observer(self._disk_activity_monitor)

        self._disk_presence_monitor.add_observer(self)
        self._disk_presence_monitor.add_observer(self._disk_activity_monitor)

        self._profiles = config.get("profiles", [])
        if not self._profiles:
            logger.warning("No profiles in configuration file, nothing to do")

    def run(self):
        logger.info("Running...")
        self._scheduler.run()

    @log_exceptions
    def on_disks_added(self, device_names: Iterable[str]):
        disk_by_device_name = {
            disk.device_name: disk for disk in self._find_monitored_disks()
        }

        for device_name in device_names:
            disk = disk_by_device_name.get(device_name)
            if disk is not None:
                self._start_disk_monitoring(disk)

    @log_exceptions
    def on_disks_removed(self, device_names: Iterable[str]):
        pass

    def _start_disk_monitoring(self, disk: _MonitoredDisk):
        self._create_spin_down_controller(disk)

    def _create_spin_down_controller(self, disk: _MonitoredDisk):
        spin_down_config = disk.profile.get("spin_down")
        if spin_down_config is None:
            logger.warning(
                "No spin down strategy found for disk %s in profile %d",
                disk.device_name,
                disk.profile_id,
            )
            return

        strategy_name = spin_down_config["when"]
        strategy_options = spin_down_config.get("options", {})
        controller = DiskSpinDownController(
            device_name=disk.device_name,
            spin_down_strategy=create_spin_down_strategy(
                strategy_name=strategy_name,
                options=strategy_options,
            ),
            spin_down_actuator=lambda: self._run_shell_command(
                command=spin_down_config["command"],
                env={"disk_path": disk.disk_path},
            ),
            scheduler=self._scheduler,
        )
        self._disk_activity_monitor.add_observer(disk.device_name, controller)
        logger.info(
            "Disk %s will be spun down when %s (%s)",
            disk.device_name,
            strategy_name,
            ", ".join(
                "{}={}".format(key, value) for key, value in strategy_options.items()
            )
            if strategy_options
            else "-",
        )

    def _find_monitored_disks(self) -> Generator[_MonitoredDisk, None, None]:
        for index, profile in enumerate(self._profiles):
            profile_id = index + 1
            disks_found = False
            for disk_path in self._find_disk_paths(profile["disks"] or []):
                disks_found = True
                yield _MonitoredDisk(
                    device_name=os.path.basename(disk_path),
                    disk_path=disk_path,
                    profile_id=profile_id,
                    profile=profile,
                )

            if not disks_found:
                logger.warning("No disks found from profile %d", profile_id)

    @staticmethod
    def _find_disk_paths(patterns: List[str]) -> Iterator[str]:
        from .lib import filesystem

        for pattern in patterns:
            for path in filesystem.find(pattern):
                if path.is_dir():
                    continue
                if str(path.parent) != "/dev":
                    logger.warning(
                        'Device file "%s" is outside /dev, skipping', str(path)
                    )
                    continue
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

        DiskMonitoringService(config).run()
        return 0
    except Error:
        log_current_exception()
        return 1


if __name__ == "__main__":
    exit(main())
