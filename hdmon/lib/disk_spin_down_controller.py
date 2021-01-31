from .disk_activity_monitor import DiskActivityObserver
from .disk_spin_down_strategy import DiskSpinDownStrategy
from .error_handling import log_exceptions
from .logger import LOGGER as logger
from .scheduler import Scheduler


class DiskSpinDownController(DiskActivityObserver):
    def __init__(
        self,
        *,
        device_name: str,
        spin_down_strategy: DiskSpinDownStrategy,
        spin_down_actuator,
        scheduler: Scheduler,
    ):
        self._device_name = device_name
        self._spin_down_strategy = spin_down_strategy
        self._spin_down_actuator = spin_down_actuator
        self._scheduler = scheduler
        self._timer_id = None

    @log_exceptions
    def on_disk_active(self):
        logger.debug("%s is active", self._device_name)
        self._cancel_timer()

    @log_exceptions
    def on_disk_idle(self):
        logger.debug("%s is idle", self._device_name)
        delay = self._spin_down_strategy.get_spin_down_delay()
        self._timer_id = self._scheduler.set_timer(delay, self._on_timer)

    @log_exceptions
    def on_disk_removed(self):
        self._cancel_timer()

    @log_exceptions
    def _on_timer(self):
        self._timer_id = None
        logger.info("Spinning down %s", self._device_name)
        self._spin_down_actuator()

    def _cancel_timer(self):
        if self._timer_id is not None:
            self._scheduler.clear_timer(self._timer_id)
            self._timer_id = None
