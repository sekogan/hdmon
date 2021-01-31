#!/usr/bin/env python3

"""
Disk monitoring and power management service
"""


from dataclasses import dataclass
from typing import Iterator, List, Iterable, Iterator, Any, Dict
import argparse
import os
import yaml

from . import plugins
from .lib.disk_activity_monitor import DiskActivityMonitor
from .lib.disk_presence_monitor import DiskPresenceMonitor, DiskPresenceObserver
from .lib.disk_stats_monitor import DiskStatsMonitor
from .lib.error_handling import Error, UsageError, log_exceptions
from .lib.logger import LOGGER as logger, log_current_exception
from .lib.scheduler import Scheduler
from .plugins.base import PluginFactory


CONFIG_PATH = "/etc/hdmon.yml"


def parse_args():
    parser = argparse.ArgumentParser(__doc__)

    parser.add_argument("-c", "--config", default=None, help="configuration file path")

    return parser.parse_args()


def load_config(path):
    with open(path) as fh:
        return yaml.safe_load(fh)


@dataclass(frozen=True)
class _Profile:
    profile_id: int
    disk_patterns: List[str]
    plugin_factories: List[PluginFactory]


@dataclass
class _MonitoredDisk:
    device_name: str  # sda
    disk_path: str  # /dev/sda
    profile: _Profile


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

        self._profiles = [
            self._create_profile(profile_id=index + 1, profile_config=profile_config)
            for index, profile_config in enumerate(config.get("profiles", []))
        ]
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
        for factory in disk.profile.plugin_factories:
            plugin = factory.create_plugin(disk.device_name, disk.disk_path)
            self._disk_activity_monitor.add_observer(disk.device_name, plugin)

    def _create_profile(
        self, profile_id: int, profile_config: Dict[str, Any]
    ) -> _Profile:
        return _Profile(
            profile_id=profile_id,
            disk_patterns=profile_config["disks"] or [],
            plugin_factories=list(self._create_plugin_factories(profile_config)),
        )

    def _create_plugin_factories(
        self, profile_config: Dict[str, Any]
    ) -> Iterator[PluginFactory]:
        for key in profile_config:
            if key in ["disks", "base"]:
                continue
            plugin = getattr(plugins, key, None)
            if plugin is None:
                logger.warning("Unknown plugin: %s, skipping", key)
                continue
            yield plugin.Factory(scheduler=self._scheduler, config=profile_config[key])

    def _find_monitored_disks(self) -> Iterator[_MonitoredDisk]:
        for profile in self._profiles:
            disks_found = False
            for disk_path in self._find_disk_paths(profile.disk_patterns):
                disks_found = True
                yield _MonitoredDisk(
                    device_name=os.path.basename(disk_path),
                    disk_path=disk_path,
                    profile=profile,
                )

            if not disks_found:
                logger.warning("No disks found from profile %d", profile.profile_id)

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


def main():
    try:
        args = parse_args()

        config_path = args.config or CONFIG_PATH
        if not os.path.isfile(config_path):
            raise UsageError(f'Cannot find configuration file "{config_path}"')
        config = load_config(config_path)

        DiskMonitoringService(config).run()
        return 0
    except Error:
        log_current_exception()
        return 1


if __name__ == "__main__":
    exit(main())
