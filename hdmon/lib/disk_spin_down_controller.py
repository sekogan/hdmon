from .disk_activity_monitor import DiskActivityObserver
from .disk_spin_down_strategy import DiskSpinDownStrategy
from .error_handling import no_exceptions
from .logger import LOGGER as logger
from .scheduler import Scheduler


class DiskSpinDownController(DiskActivityObserver):
    def __init__(
        self,
        *,
        disk_path: str,
        spin_down_strategy: DiskSpinDownStrategy,
        spin_down_actuator,
        scheduler: Scheduler,
    ):
        self._disk_path = disk_path
        self._spin_down_strategy = spin_down_strategy
        self._spin_down_actuator = spin_down_actuator
        self._scheduler = scheduler
        self._timer_id = None

    @no_exceptions
    def on_disk_active(self):
        if self._timer_id is not None:
            self._scheduler.clear_timer(self._timer_id)
            self._timer_id = None

    @no_exceptions
    def on_disk_idle(self):
        delay = self._spin_down_strategy.get_spin_down_delay()
        self._timer_id = self._scheduler.set_timer(delay, self._on_timer)

    @no_exceptions
    def _on_timer(self):
        logger.info("Spinning down %s", self.disk_path)
        self._spin_down_actuator()
