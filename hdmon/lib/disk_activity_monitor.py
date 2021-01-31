from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Iterable, Optional
import collections
import os

from .disk_stats import iter_disk_stats, DiskCounters, DeviceNameAndCounters
from .error_handling import log_exceptions
from .scheduler import Scheduler


class DiskPresenceObserver(ABC):
    @abstractmethod
    def on_disks_added(self, device_names: Iterable[str]):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()

    @abstractmethod
    def on_disks_removed(self, device_names: Iterable[str]):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()


class DiskActivityObserver(ABC):
    @abstractmethod
    def on_disk_active(self):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()

    @abstractmethod
    def on_disk_idle(self):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()


_ActivityObserverList = List[DiskActivityObserver]
_ActivityObserverMap = Dict[str, _ActivityObserverList]


@dataclass
class _Disk:
    counters: DiskCounters
    is_idle: bool


class DiskActivityMonitor(DiskPresenceObserver):
    _POLLING_INTERVAL = 1 * 60  # 1 minute

    def __init__(self, *, scheduler: Scheduler):
        self._scheduler = scheduler
        self._presence_observers: List[DiskPresenceObserver] = [self]
        self._activity_observers: _ActivityObserverMap = collections.defaultdict(list)
        self._disks: Dict[str, Optional[_Disk]] = {}
        self._set_timer(delay=0)

    def add_presence_observer(self, observer: DiskPresenceObserver):
        self._presence_observers.append(observer)

    def add_activity_observer(self, disk_path: str, observer: DiskActivityObserver):
        self._activity_observers[os.path.basename(disk_path)].append(observer)

    def remove_activity_observer(self, disk_path: str, observer: DiskActivityObserver):
        self._activity_observers[os.path.basename(disk_path)].remove(observer)

    @log_exceptions
    def _on_timer(self):
        self._set_timer(delay=self._POLLING_INTERVAL)
        disk_stats = list(iter_disk_stats())
        self._update_presence_information(disk_stats)
        self._update_activity_information(disk_stats)

    def _update_presence_information(self, disk_stats: Iterable[DeviceNameAndCounters]):
        previous_disks = set(self._disks)
        current_disks = set(device_name for device_name, _counters in disk_stats)
        possibly_replaced_disks = set(
            device_name
            for device_name, counters in disk_stats
            if (
                device_name in self._disks
                and self._is_disk_replaced(self._disks[device_name].counters, counters)
            )
        )
        removed_disks = (previous_disks - current_disks) | possibly_replaced_disks
        added_disks = (current_disks - previous_disks) | possibly_replaced_disks
        if removed_disks:
            for observer in self._presence_observers:
                observer.on_disks_removed(removed_disks)
        if added_disks:
            for observer in self._presence_observers:
                observer.on_disks_added(added_disks)

    def on_disks_added(self, device_names):
        for device_name in device_names:
            self._disks[device_name] = None

    def on_disks_removed(self, device_names):
        for device_name in device_names:
            del self._disks[device_name]

    def _update_activity_information(self, disk_stats: Iterable[DeviceNameAndCounters]):
        for device_name, counters in disk_stats:
            disk = self._disks[device_name]
            if disk is None:
                self._disks[device_name] = _Disk(counters=counters, is_idle=False)
                continue
            was_idle = disk.is_idle
            is_idle = self._is_disk_idle(disk.counters, counters)
            disk.counters = counters
            disk.is_idle = is_idle
            if was_idle == is_idle:
                continue
            observers = self._activity_observers.get(device_name, [])
            for observer in observers:
                if is_idle:
                    observer.on_disk_idle()
                else:
                    observer.on_disk_active()

    def _set_timer(self, delay: int):
        self._scheduler.set_timer(delay, self._on_timer)

    @staticmethod
    def _is_disk_replaced(previous: DiskCounters, current: DiskCounters) -> bool:
        # This heuristic can give false positives because counters are integers
        # that can overflow on long running systems.
        return (
            previous.sectors_read > current.sectors_read
            or previous.sectors_written > current.sectors_written
        )

    @staticmethod
    def _is_disk_idle(previous: DiskCounters, current: DiskCounters) -> bool:
        return (
            previous.sectors_read == current.sectors_read
            and previous.sectors_written == current.sectors_written
        )
