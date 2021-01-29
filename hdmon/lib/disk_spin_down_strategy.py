from abc import ABC, abstractmethod

from .human_readable import duration_to_seconds


def create(strategy_name, options):
    if strategy_name == "idle":
        return _IdleStrategy(options)
    raise ValueError(f'Unknown spin down strategy: "{strategy_name}"')


class DiskSpinDownStrategy(ABC):
    @abstractmethod
    def get_spin_down_delay(self):
        raise NotImplementedError()


class _IdleStrategy(DiskSpinDownStrategy):
    def __init__(self, options):
        self._delay = duration_to_seconds(options["delay"])

    def get_spin_down_delay(self):
        return self._delay
