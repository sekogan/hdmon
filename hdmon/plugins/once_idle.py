from ..lib import human_readable
from ..lib import shell
from ..lib.error_handling import log_exceptions
from ..lib.logger import LOGGER as logger
from ..lib.scheduler import Scheduler
from .base import Plugin, PluginFactory, PluginConfig


class Factory(PluginFactory):
    def create_plugin(self, device_name: str, disk_path: str) -> Plugin:
        return OnceIdle(
            device_name=device_name,
            disk_path=disk_path,
            scheduler=self._scheduler,
            config=self._config,
        )


class OnceIdle(Plugin):
    def __init__(
        self,
        *,
        device_name: str,
        disk_path: str,
        scheduler: Scheduler,
        config: PluginConfig,
    ):
        self._device_name = device_name
        self._disk_path = disk_path
        self._scheduler = scheduler
        human_readable_delay = config["delay"]
        self._delay = human_readable.duration_to_seconds(human_readable_delay)
        self._command = config["run"]
        self._timer_id = None
        logger.info(
            '%s once idle for %d will run "%s"',
            device_name,
            human_readable_delay,
            self._command,
        )

    @log_exceptions
    def on_disk_active(self):
        self._cancel_timer()

    @log_exceptions
    def on_disk_idle(self):
        self._timer_id = self._scheduler.set_timer(self._delay, self._on_timer)

    @log_exceptions
    def on_disk_removed(self):
        self._cancel_timer()

    @log_exceptions
    def _on_timer(self):
        self._timer_id = None
        shell.run(self.command, env={"disk_path": self._disk_path})

    def _cancel_timer(self):
        if self._timer_id is not None:
            self._scheduler.clear_timer(self._timer_id)
            self._timer_id = None