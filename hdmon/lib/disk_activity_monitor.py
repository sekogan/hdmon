from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List
import collections
import os

from .disk_stats import iter_disk_stats, DiskStat
from .error_handling import log_exceptions
from .scheduler import Scheduler


class DiskActivityObserver(ABC):
    @abstractmethod
    def on_disk_active(self):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()

    @abstractmethod
    def on_disk_idle(self):
        """Shouldn't raise exceptions"""
        raise NotImplementedError()


_ObserverList = List[DiskActivityObserver]


@dataclass
class _DiskState:
    last_stat: DiskStat
    is_idle: bool = False


class DiskActivityMonitor:
    _POLLING_INTERVAL = 1 * 60  # 1 minute

    def __init__(self, *, scheduler: Scheduler):
        self._scheduler = scheduler
        self._observers: Dict[str, _ObserverList] = collections.defaultdict(list)
        self._disk_state: Dict[str, _DiskState] = {}
        self._set_timer(delay=0)

    def add_observer(self, disk_path: str, observer: DiskActivityObserver):
        self._observers[os.path.basename(disk_path)].append(observer)

    @log_exceptions
    def _on_timer(self):
        for current_stat in iter_disk_stats():
            disk_state = self._disk_state.get(current_stat.device_name)
            if disk_state is None:
                self._disk_state[current_stat.device_name] = _DiskState(current_stat)
                continue
            was_idle = disk_state.is_idle
            is_idle = self._is_idle(disk_state.last_stat, current_stat)
            disk_state.last_stat = current_stat
            disk_state.is_idle = is_idle
            if was_idle == is_idle:
                continue
            for observer in self._observers.get(current_stat.device_name, []):
                if is_idle:
                    observer.on_disk_idle()
                else:
                    observer.on_disk_active()
        self._set_timer(delay=self._POLLING_INTERVAL)

    def _set_timer(self, delay: int):
        self._scheduler.set_timer(delay, self._on_timer)

    @staticmethod
    def _is_idle(last_stat: DiskStat, current_stat: DiskStat) -> bool:
        return (
            last_stat.sectors_read == current_stat.sectors_read
            and last_stat.sectors_written == current_stat.sectors_written
        )
