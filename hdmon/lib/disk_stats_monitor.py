from abc import ABC, abstractmethod
from typing import List, Iterable

from .disk_stats import iter_disk_stats, DeviceNameAndCounters
from .error_handling import log_exceptions
from .scheduler import Scheduler


class DiskStatsObserver(ABC):
    @abstractmethod
    def on_disk_stats_updated(self, disk_stats: Iterable[DeviceNameAndCounters]):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()


class DiskStatsMonitor:
    _POLLING_INTERVAL = 1 * 60  # 1 minute

    def __init__(self, *, scheduler: Scheduler):
        self._scheduler = scheduler
        self._observers: List[DiskStatsObserver] = []
        self._set_timer(delay=0)

    def add_observer(self, observer: DiskStatsObserver):
        self._observers.append(observer)

    @log_exceptions
    def _on_timer(self):
        self._set_timer(delay=self._POLLING_INTERVAL)
        disk_stats = list(iter_disk_stats())
        for observer in self._observers:
            observer.on_disk_stats_updated(disk_stats)

    def _set_timer(self, delay: int):
        self._scheduler.set_timer(delay, self._on_timer)
