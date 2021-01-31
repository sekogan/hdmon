from typing import Dict
from unittest import mock
import unittest

from hdmon.lib.disk_activity_monitor import DiskActivityMonitor
from hdmon.lib.disk_stats import DiskCounters


class DiskActivityMonitorTestCase(unittest.TestCase):
    def setUp(self):
        self._disk_counters: Dict[str, DiskCounters] = {}
        self.monitor = DiskActivityMonitor()

    def notify_monitor_about_current_disk_stats(self):
        self.monitor.on_disk_stats_updated(self._disk_counters.items())

    def add_disk(self, device_name, counters):
        self.monitor.on_disks_added([device_name])
        self._disk_counters[device_name] = counters

    def increment_disk_counters(self, device_name, sectors_read=0, sectors_written=0):
        current_counters = self._disk_counters[device_name]
        self._disk_counters[device_name] = DiskCounters(
            sectors_read=current_counters.sectors_read + sectors_read,
            sectors_written=current_counters.sectors_written + sectors_written,
        )

    def make_disk_active(self, device_name):
        self.notify_monitor_about_current_disk_stats()
        self.increment_disk_counters(device_name, sectors_read=1)
        self.notify_monitor_about_current_disk_stats()

    def make_all_disks_idle(self):
        self.notify_monitor_about_current_disk_stats()
        self.notify_monitor_about_current_disk_stats()

    def test_no_disks(self):
        observer = mock.Mock()
        self.monitor.add_observer("sda", observer)

        self.make_all_disks_idle()
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.assert_not_called()

    def test_does_not_notify_activity_observers_on_first_update(self):
        observer = mock.Mock()
        self.monitor.add_observer("sda", observer)

        self.add_disk("sda", DiskCounters(sectors_read=0, sectors_written=0))
        self.notify_monitor_about_current_disk_stats()
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.assert_not_called()

    def test_detects_idle_disk_on_second_update(self):
        observer = mock.Mock()
        self.monitor.add_observer("sda", observer)

        self.add_disk("sda", DiskCounters(sectors_read=0, sectors_written=0))
        self.notify_monitor_about_current_disk_stats()
        self.notify_monitor_about_current_disk_stats()
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.called_once()

    def test_detects_active_disk_on_second_update(self):
        observer = mock.Mock()
        self.monitor.add_observer("sda", observer)

        self.add_disk("sda", DiskCounters(sectors_read=0, sectors_written=0))
        self.notify_monitor_about_current_disk_stats()
        self.increment_disk_counters("sda", sectors_read=1)
        self.notify_monitor_about_current_disk_stats()
        observer.on_disk_active.called_once()
        observer.on_disk_idle.assert_not_called()

    def test_detects_idle_disk_once(self):
        self.add_disk("sda", DiskCounters(sectors_read=0, sectors_written=0))
        self.make_disk_active("sda")

        observer = mock.Mock()
        self.monitor.add_observer("sda", observer)

        observer.reset_mock()
        self.notify_monitor_about_current_disk_stats()
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.called_once()

        self.notify_monitor_about_current_disk_stats()
        self.notify_monitor_about_current_disk_stats()
        self.notify_monitor_about_current_disk_stats()
        observer.on_disk_active.assert_not_called()
        observer.on_disk_idle.called_once()

    def test_detects_active_disk_by_reads(self):
        self.add_disk("sda", DiskCounters(sectors_read=0, sectors_written=0))
        self.make_all_disks_idle()

        self.increment_disk_counters("sda", sectors_read=1)

        observer = mock.Mock()
        self.monitor.add_observer("sda", observer)
        observer.reset_mock()
        self.notify_monitor_about_current_disk_stats()
        observer.on_disk_active.assert_called_once()
        observer.on_disk_idle.assert_not_called()

    def test_detects_active_disk_by_writes(self):
        self.add_disk("sda", DiskCounters(sectors_read=0, sectors_written=0))
        self.make_all_disks_idle()

        self.increment_disk_counters("sda", sectors_written=1)

        observer = mock.Mock()
        self.monitor.add_observer("sda", observer)
        observer.reset_mock()
        self.notify_monitor_about_current_disk_stats()
        observer.on_disk_active.assert_called_once()
        observer.on_disk_idle.assert_not_called()

    def test_detects_active_disk_once(self):
        self.add_disk("sda", DiskCounters(sectors_read=0, sectors_written=0))
        self.make_all_disks_idle()

        self.increment_disk_counters("sda", sectors_read=1)

        observer = mock.Mock()
        self.monitor.add_observer("sda", observer)
        observer.reset_mock()
        self.notify_monitor_about_current_disk_stats()
        observer.on_disk_active.assert_called_once()
        observer.on_disk_idle.assert_not_called()

        self.increment_disk_counters("sda", sectors_read=1)
        self.notify_monitor_about_current_disk_stats()
        self.increment_disk_counters("sda", sectors_read=1)
        self.notify_monitor_about_current_disk_stats()
        self.increment_disk_counters("sda", sectors_read=1)
        self.notify_monitor_about_current_disk_stats()
        observer.on_disk_active.assert_called_once()
        observer.on_disk_idle.assert_not_called()

    def test_notifies_multiple_disk_observers(self):
        self.add_disk("sda", DiskCounters(sectors_read=0, sectors_written=0))
        self.make_all_disks_idle()

        self.increment_disk_counters("sda", sectors_written=1)

        observer1 = mock.Mock()
        self.monitor.add_observer("sda", observer1)
        observer1.reset_mock()
        observer2 = mock.Mock()
        self.monitor.add_observer("sda", observer2)
        observer2.reset_mock()
        self.notify_monitor_about_current_disk_stats()
        observer1.on_disk_active.assert_called_once()
        observer2.on_disk_active.assert_called_once()

    def test_notifies_specific_disk_observers(self):
        self.add_disk("sda", DiskCounters(sectors_read=0, sectors_written=0))
        self.add_disk("sdb", DiskCounters(sectors_read=0, sectors_written=0))
        self.make_all_disks_idle()

        sda_observer = mock.Mock()
        self.monitor.add_observer("sda", sda_observer)
        sdb_observer = mock.Mock()
        self.monitor.add_observer("sdb", sdb_observer)

        sda_observer.reset_mock()
        sdb_observer.reset_mock()
        self.increment_disk_counters("sda", sectors_written=1)
        self.notify_monitor_about_current_disk_stats()
        sda_observer.on_disk_active.assert_called_once()
        sdb_observer.on_disk_active.assert_not_called()

        self.increment_disk_counters("sdb", sectors_written=1)
        self.notify_monitor_about_current_disk_stats()
        sda_observer.on_disk_active.assert_called_once()
        sdb_observer.on_disk_active.assert_called_once()

    def test_notifies_new_observers_about_current_disks(self):
        self.add_disk("sda", DiskCounters(sectors_read=0, sectors_written=0))
        self.add_disk("sdb", DiskCounters(sectors_read=0, sectors_written=0))
        self.make_all_disks_idle()

        self.make_disk_active("sdb")

        sda_observer = mock.Mock()
        self.monitor.add_observer("sda", sda_observer)
        sda_observer.on_disk_idle.assert_called_once()
        sda_observer.on_disk_active.assert_not_called()

        sdb_observer = mock.Mock()
        self.monitor.add_observer("sdb", sdb_observer)
        sdb_observer.on_disk_active.assert_called_once()
        sdb_observer.on_disk_idle.assert_not_called()

        sdc_observer = mock.Mock()
        self.monitor.add_observer("sdc", sdc_observer)
        sdc_observer.on_disk_active.assert_not_called()
        sdc_observer.on_disk_idle.assert_not_called()


if __name__ == "__main__":
    unittest.main()
