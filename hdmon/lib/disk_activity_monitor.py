from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Iterable
import collections

from .disk_presence_monitor import DiskPresenceObserver
from .disk_stats import DiskCounters, DeviceNameAndCounters
from .disk_stats_monitor import DiskStatsObserver
from .error_handling import log_exceptions
from .logger import LOGGER as logger


class DiskActivityObserver(ABC):
    @abstractmethod
    def on_disk_active(self):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()

    @abstractmethod
    def on_disk_idle(self):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()

    @abstractmethod
    def on_disk_removed(self):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()


_ActivityObserverList = List[DiskActivityObserver]
_ActivityObserverMap = Dict[str, _ActivityObserverList]


@dataclass
class _Disk:
    counters: DiskCounters
    is_idle: bool


class DiskActivityMonitor(DiskStatsObserver, DiskPresenceObserver):
    def __init__(self):
        self._observers: _ActivityObserverMap = collections.defaultdict(list)
        self._disks: Dict[str, _Disk] = {}

    def add_observer(self, device_name: str, observer: DiskActivityObserver):
        self._observers[device_name].append(observer)
        disk = self._disks.get(device_name)
        if disk is not None:
            if len(self._observers[device_name]) == 1:
                self._log_disk_state(device_name, disk.is_idle)
            self._notify(observer, disk.is_idle)

    @log_exceptions
    def on_disks_added(self, device_names: Iterable[str]):
        pass

    @log_exceptions
    def on_disks_removed(self, device_names: Iterable[str]):
        for device_name in device_names:
            self._disks.pop(device_name, None)
            observers = self._observers.pop(device_name, [])
            for observer in observers:
                observer.on_disk_removed()

    @log_exceptions
    def on_disk_stats_updated(self, disk_stats: Iterable[DeviceNameAndCounters]):
        for device_name, counters in disk_stats:
            disk = self._disks.get(device_name)
            if disk is None:
                self._disks[device_name] = _Disk(counters=counters, is_idle=False)
                continue

            was_idle = disk.is_idle
            is_idle = self._is_disk_idle(disk.counters, counters)
            disk.counters = counters
            disk.is_idle = is_idle
            if was_idle == is_idle:
                continue

            observers = self._observers.get(device_name, [])

            if observers:
                self._log_disk_state(device_name, is_idle)

            for observer in observers:
                self._notify(observer, is_idle)

    @staticmethod
    def _notify(observer, is_idle):
        if is_idle:
            observer.on_disk_idle()
        else:
            observer.on_disk_active()

    @staticmethod
    def _log_disk_state(device_name, is_idle):
        logger.debug("%s is %s", device_name, "idle" if is_idle else "active")

    @staticmethod
    def _is_disk_idle(previous: DiskCounters, current: DiskCounters) -> bool:
        return (
            previous.sectors_read == current.sectors_read
            and previous.sectors_written == current.sectors_written
        )
