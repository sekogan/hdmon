from ..lib.disk_activity_monitor import DiskActivityObserver
from ..lib.scheduler import Scheduler
from abc import ABC, abstractmethod
from typing import Dict, Any


class Plugin(DiskActivityObserver):
    pass


PluginConfig = Dict[str, Any]


class PluginFactory(ABC):
    def __init__(self, scheduler: Scheduler, config: PluginConfig):
        self._scheduler = scheduler
        self._config = config

    @abstractmethod
    def create_plugin(self, device_name: str, disk_path: str) -> Plugin:
        raise NotImplementedError()
