from abc import ABC, abstractmethod
from typing import Dict, List, Iterable

from .disk_stats import DiskCounters, DeviceNameAndCounters
from .disk_stats_monitor import DiskStatsObserver
from .error_handling import log_exceptions
from .logger import LOGGER as logger


class DiskPresenceObserver(ABC):
    @abstractmethod
    def on_disks_added(self, device_names: Iterable[str]):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()

    @abstractmethod
    def on_disks_removed(self, device_names: Iterable[str]):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()


class DiskPresenceMonitor(DiskStatsObserver):
    def __init__(self):
        self._observers: List[DiskPresenceObserver] = []
        self._disks: Dict[str, DiskCounters] = {}

    def add_observer(self, observer: DiskPresenceObserver):
        self._observers.append(observer)
        if self._disks:
            observer.on_disks_added(self._disks)

    @log_exceptions
    def on_disk_stats_updated(self, disk_stats: Iterable[DeviceNameAndCounters]):
        if self._has_changes(disk_stats):
            self._apply_changes(disk_stats)
        self._update_counters(disk_stats)

    def _has_changes(self, disk_stats: Iterable[DeviceNameAndCounters]):
        # Should be as fast as possible
        disk_counter = 0
        for device_name, counters in disk_stats:
            disk_counter += 1
            previous_counters = self._disks.get(device_name)
            if previous_counters is None or self._is_disk_replaced(
                previous_counters, counters
            ):
                return True
        return disk_counter != len(self._disks)

    def _apply_changes(self, disk_stats: Iterable[DeviceNameAndCounters]):
        disks_previous = set(self._disks)
        disks_current = set(device_name for device_name, _counters in disk_stats)
        disks_replaced = set(
            device_name
            for device_name, counters in disk_stats
            if (
                device_name in self._disks
                and self._is_disk_replaced(self._disks[device_name], counters)
            )
        )
        disks_added = (disks_current - disks_previous) | disks_replaced
        disks_removed = (disks_previous - disks_current) | disks_replaced

        if disks_removed:
            for device_name in disks_removed:
                self._log_disk_state(device_name, is_offline=True)
                del self._disks[device_name]
            for observer in self._observers:
                observer.on_disks_removed(disks_removed)
        if disks_added:
            for device_name in disks_removed:
                self._log_disk_state(device_name, is_offline=False)
                # Disk are added to self._disks in _update_counters
            for observer in self._observers:
                observer.on_disks_added(disks_added)

    def _update_counters(self, disk_stats: Iterable[DeviceNameAndCounters]):
        for device_name, counters in disk_stats:
            self._disks[device_name] = counters

    @staticmethod
    def _is_disk_replaced(previous: DiskCounters, current: DiskCounters) -> bool:
        # This heuristic can give false positives because counters are integers
        # that can overflow on long running systems.
        return (
            previous.sectors_read > current.sectors_read
            or previous.sectors_written > current.sectors_written
        )

    @staticmethod
    def _log_disk_state(device_name, is_offline):
        logger.info("%s is %s", device_name, "offline" if is_offline else "online")
