from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Iterable, Set
import collections
import os

from .disk_stats import iter_disk_stats, DiskCounters
from .error_handling import log_exceptions
from .scheduler import Scheduler


class DiskPresenceObserver(ABC):
    @abstractmethod
    def on_disks_added(self, disk_paths: Iterable[str]):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()

    @abstractmethod
    def on_disks_removed(self, disk_paths: Iterable[str]):
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
class _DiskState:
    last_counters: DiskCounters
    is_idle: bool = False


class DiskActivityMonitor:
    _POLLING_INTERVAL = 1 * 60  # 1 minute

    def __init__(self, *, scheduler: Scheduler):
        self._scheduler = scheduler
        self._presence_observers: List[DiskPresenceObserver] = []
        self._activity_observers: _ActivityObserverMap = collections.defaultdict(list)
        self._seen_disks: Set[str] = set()
        self._disk_state: Dict[str, _DiskState] = {}
        self._set_timer(delay=0)

    def add_presence_observer(self, observer: DiskPresenceObserver):
        self._presence_observers.append(observer)

    def add_activity_observer(self, disk_path: str, observer: DiskActivityObserver):
        self._activity_observers[os.path.basename(disk_path)].append(observer)

    def remove_activity_observer(self, disk_path: str, observer: DiskActivityObserver):
        self._activity_observers[os.path.basename(disk_path)].remove(observer)

    @log_exceptions
    def _on_timer(self):
        disk_stats = list(iter_disk_stats())
        self._update_presence_observers(disk_stats)
        self._update_activity_observers(disk_stats)
        self._set_timer(delay=self._POLLING_INTERVAL)

    def _update_presence_observers(self, disk_stats: Iterable[DiskCounters]):
        previously_seen_disks = self._seen_disks
        seen_disks: Set[str] = set()
        self._seen_disks = seen_disks
        possibly_changed_disks = set()
        for disk_counters in disk_stats:
            seen_disks.add(disk_counters.device_name)
            disk_state = self._disk_state.get(disk_counters.device_name)
            if disk_state is not None:
                last_counters = disk_state.last_counters
                if (
                    last_counters.sectors_read > disk_counters.sectors_read
                    or last_counters.sectors_written > disk_counters.sectors_written
                ):
                    possibly_changed_disks.add(disk_counters.device_name)
        removed_disks = (previously_seen_disks - seen_disks) | possibly_changed_disks
        added_disks = (seen_disks - previously_seen_disks) | possibly_changed_disks
        if removed_disks:
            for device_name in removed_disks:
                del self._disk_state[device_name]
            for observer in self._presence_observers:
                observer.on_disks_removed(removed_disks)
        if added_disks:
            for observer in self._presence_observers:
                observer.on_disks_added(added_disks)

    def _update_activity_observers(self, disk_stats: Iterable[DiskCounters]):
        for current_counters in disk_stats:
            disk_state = self._disk_state.get(current_counters.device_name)
            if disk_state is None:
                self._disk_state[current_counters.device_name] = _DiskState(
                    current_counters
                )
                continue
            was_idle = disk_state.is_idle
            is_idle = self._is_idle(disk_state.last_counters, current_counters)
            disk_state.last_counters = current_counters
            disk_state.is_idle = is_idle
            if was_idle == is_idle:
                continue
            observers = self._activity_observers.get(current_counters.device_name, [])
            for observer in observers:
                if is_idle:
                    observer.on_disk_idle()
                else:
                    observer.on_disk_active()

    def _set_timer(self, delay: int):
        self._scheduler.set_timer(delay, self._on_timer)

    @staticmethod
    def _is_idle(last_counters: DiskCounters, current_counters: DiskCounters) -> bool:
        return (
            last_counters.sectors_read == current_counters.sectors_read
            and last_counters.sectors_written == current_counters.sectors_written
        )
