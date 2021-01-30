from typing import Dict
from unittest import mock
import unittest

from hdmon.lib.disk_activity_monitor import DiskActivityMonitor
from hdmon.lib.disk_stats import DiskCounters


class DiskActivityMonitorTestCase(unittest.TestCase):
    def setUp(self):
        self.disk_counters: Dict[str, DiskCounters] = {}
        patcher = mock.patch(
            "hdmon.lib.disk_activity_monitor.iter_disk_stats",
            side_effect=lambda: self.disk_counters.items(),
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.scheduler = mock.Mock()

    def set_disk_counters(self, device_name, sectors_read=0, sectors_written=0):
        self.disk_counters[device_name] = DiskCounters(
            sectors_read=sectors_read, sectors_written=sectors_written
        )

    def increment_disk_counters(self, device_name, sectors_read=0, sectors_written=0):
        current_counters = self.disk_counters[device_name]
        self.disk_counters[device_name] = DiskCounters(
            sectors_read=current_counters.sectors_read + sectors_read,
            sectors_written=current_counters.sectors_written + sectors_written,
        )

    def make_disk_active(self, device_name, monitor):
        monitor._on_timer()
        self.increment_disk_counters(device_name, 1, 1)
        monitor._on_timer()

    def make_all_disks_idle(self, monitor):
        monitor._on_timer()
        monitor._on_timer()

    def test_empty_disk_counters(self):
        monitor = DiskActivityMonitor(scheduler=self.scheduler)
        observer = mock.Mock()
        monitor.add_activity_observer("/dev/sda", observer)

        self.disk_counters = {}
        self.make_all_disks_idle(monitor)
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.assert_not_called()

    def test_detects_idle_disk_once_at_startup(self):
        monitor = DiskActivityMonitor(scheduler=self.scheduler)
        observer = mock.Mock()
        monitor.add_activity_observer("/dev/sda", observer)

        self.set_disk_counters(device_name="sda", sectors_read=100, sectors_written=100)
        monitor._on_timer()
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.assert_not_called()

        monitor._on_timer()
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.called_once()

        monitor._on_timer()
        monitor._on_timer()
        monitor._on_timer()
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.called_once()

    def test_detects_idle_disk_once(self):
        monitor = DiskActivityMonitor(scheduler=self.scheduler)

        self.set_disk_counters(device_name="sda", sectors_read=100, sectors_written=100)
        self.make_disk_active(device_name="sda", monitor=monitor)

        observer = mock.Mock()
        monitor.add_activity_observer("/dev/sda", observer)

        monitor._on_timer()
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.called_once()

        monitor._on_timer()
        monitor._on_timer()
        monitor._on_timer()
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.called_once()

    def test_detects_active_disk_by_reads(self):
        monitor = DiskActivityMonitor(scheduler=self.scheduler)

        self.set_disk_counters(device_name="sda", sectors_read=100, sectors_written=100)
        self.make_all_disks_idle(monitor)

        self.increment_disk_counters(device_name="sda", sectors_read=1)

        observer = mock.Mock()
        monitor.add_activity_observer("/dev/sda", observer)
        monitor._on_timer()
        observer.on_disk_active.assert_called_once()
        observer.on_disk_idle.assert_not_called()

    def test_detects_active_disk_by_writes(self):
        monitor = DiskActivityMonitor(scheduler=self.scheduler)

        self.set_disk_counters(device_name="sda", sectors_read=100, sectors_written=100)
        self.make_all_disks_idle(monitor)

        self.increment_disk_counters(device_name="sda", sectors_written=1)

        observer = mock.Mock()
        monitor.add_activity_observer("/dev/sda", observer)
        monitor._on_timer()
        observer.on_disk_active.assert_called_once()
        observer.on_disk_idle.assert_not_called()

    def test_notifies_multiple_disk_observers(self):
        monitor = DiskActivityMonitor(scheduler=self.scheduler)

        self.set_disk_counters(device_name="sda", sectors_read=100, sectors_written=100)
        self.make_all_disks_idle(monitor)

        self.increment_disk_counters(device_name="sda", sectors_written=1)

        observer1 = mock.Mock()
        monitor.add_activity_observer("/dev/sda", observer1)
        observer2 = mock.Mock()
        monitor.add_activity_observer("/dev/sda", observer2)
        monitor._on_timer()
        observer1.on_disk_active.assert_called_once()
        observer2.on_disk_active.assert_called_once()

    def test_notifies_specific_disk_observers(self):
        monitor = DiskActivityMonitor(scheduler=self.scheduler)

        self.set_disk_counters(device_name="sda", sectors_read=100, sectors_written=100)
        self.set_disk_counters(device_name="sdb", sectors_read=100, sectors_written=100)
        self.make_all_disks_idle(monitor)

        self.increment_disk_counters(device_name="sda", sectors_written=1)

        sda_observer = mock.Mock()
        monitor.add_activity_observer("/dev/sda", sda_observer)
        sdb_observer = mock.Mock()
        monitor.add_activity_observer("/dev/sdb", sdb_observer)
        monitor._on_timer()
        sda_observer.on_disk_active.assert_called_once()
        sdb_observer.on_disk_active.assert_not_called()


if __name__ == "__main__":
    unittest.main()
