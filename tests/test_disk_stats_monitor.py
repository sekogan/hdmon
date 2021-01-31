from typing import Dict
from unittest import mock
import unittest

from hdmon.lib.disk_stats_monitor import DiskStatsMonitor
from hdmon.lib.disk_stats import DiskCounters


class DiskStatsMonitorTestCase(unittest.TestCase):
    def setUp(self):
        self._disk_counters: Dict[str, DiskCounters] = {}
        patcher = mock.patch(
            "hdmon.lib.disk_stats_monitor.iter_disk_stats",
            side_effect=lambda: self._disk_counters.items(),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.scheduler = mock.Mock()
        self.monitor = DiskStatsMonitor(scheduler=self.scheduler)

    def set_disk(self, device_name, counters):
        self._disk_counters[device_name] = counters

    def test_sets_initial_timer(self):
        self.scheduler.set_timer.assert_called()

    def test_sets_timer_again_on_timer(self):
        self.scheduler.set_timer.reset_mock()
        self.monitor._on_timer()
        self.scheduler.set_timer.assert_called()

    def test_calls_observers(self):
        observer1 = mock.Mock()
        observer2 = mock.Mock()
        self.monitor.add_observer(observer1)
        self.monitor.add_observer(observer2)
        self.monitor._on_timer()
        observer1.on_disk_stats_updated.assert_called_once()
        observer2.on_disk_stats_updated.assert_called_once()


if __name__ == "__main__":
    unittest.main()
