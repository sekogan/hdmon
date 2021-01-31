from typing import Dict, Iterable
from unittest import mock
import unittest

from hdmon.lib.disk_presence_monitor import DiskPresenceMonitor
from hdmon.lib.disk_stats import DiskCounters, DeviceNameAndCounters


class DiskPresenceMonitorTestCase(unittest.TestCase):
    def setUp(self):
        self._disk_counters: Dict[str, DiskCounters] = {}
        self.monitor = DiskPresenceMonitor()

    def notify_monitor_about_current_disk_stats(self):
        self.monitor.on_disk_stats_updated(self._disk_counters.items())

    def add_disks(self, disks: Iterable[DeviceNameAndCounters]):
        for device_name, counters in disks:
            self._disk_counters[device_name] = counters

    def remove_disks(self, device_names):
        for device_name in device_names:
            del self._disk_counters[device_name]

    def set_disk_counters(self, device_name, counters):
        self._disk_counters[device_name] = counters

    def test_detects_added_disks(self):
        observer = mock.Mock()
        self.monitor.add_observer(observer)

        self.add_disks(
            [
                ("sda", DiskCounters(0, 0)),
                ("sdb", DiskCounters(0, 0)),
            ]
        )
        self.notify_monitor_about_current_disk_stats()
        observer.on_disks_added.assert_called_once()
        self.assertCountEqual(
            ["sda", "sdb"], list(observer.on_disks_added.call_args[0][0])
        )

        observer.reset_mock()
        self.add_disks(
            [
                ("sdc", DiskCounters(0, 0)),
            ]
        )
        self.notify_monitor_about_current_disk_stats()
        observer.on_disks_added.assert_called_once()
        self.assertCountEqual(["sdc"], list(observer.on_disks_added.call_args[0][0]))

    def test_detects_removed_disks(self):
        observer = mock.Mock()
        self.monitor.add_observer(observer)

        self.add_disks(
            [
                ("sda", DiskCounters(0, 0)),
                ("sdb", DiskCounters(0, 0)),
                ("sdc", DiskCounters(0, 0)),
            ]
        )
        self.notify_monitor_about_current_disk_stats()
        observer.on_disks_removed.assert_not_called()

        self.remove_disks(["sda", "sdc"])
        self.notify_monitor_about_current_disk_stats()
        observer.on_disks_removed.assert_called_once()
        self.assertCountEqual(
            ["sda", "sdc"], list(observer.on_disks_removed.call_args[0][0])
        )

        observer.reset_mock()
        self.remove_disks(["sdb"])
        self.notify_monitor_about_current_disk_stats()
        observer.on_disks_removed.assert_called_once()
        self.assertCountEqual(["sdb"], list(observer.on_disks_removed.call_args[0][0]))

    def test_does_nothing_if_nothing_changes(self):
        self.add_disks(
            [
                ("sda", DiskCounters(0, 0)),
                ("sdb", DiskCounters(0, 0)),
                ("sdc", DiskCounters(0, 0)),
            ]
        )
        self.notify_monitor_about_current_disk_stats()

        observer = mock.Mock()
        self.monitor.add_observer(observer)

        observer.reset_mock()
        self.notify_monitor_about_current_disk_stats()
        observer.on_disks_added.assert_not_called()
        observer.on_disks_removed.assert_not_called()

        self.set_disk_counters("sda", DiskCounters(100, 100))
        self.set_disk_counters("sdb", DiskCounters(100, 100))
        self.notify_monitor_about_current_disk_stats()
        observer.on_disks_added.assert_not_called()
        observer.on_disks_removed.assert_not_called()

    def test_notifies_new_observers_about_current_disks(self):
        observer = mock.Mock()
        self.monitor.add_observer(observer)
        observer.on_disks_added.assert_not_called()

        self.add_disks(
            [
                ("sda", DiskCounters(0, 0)),
                ("sdb", DiskCounters(0, 0)),
            ]
        )
        self.notify_monitor_about_current_disk_stats()

        observer = mock.Mock()
        self.monitor.add_observer(observer)

        observer.on_disks_added.assert_called_once()
        self.assertCountEqual(
            ["sda", "sdb"], list(observer.on_disks_added.call_args[0][0])
        )

    def test_detects_replaced_disks(self):
        self.add_disks(
            [
                ("sda", DiskCounters(0, 0)),
                ("sdb", DiskCounters(0, 0)),
                ("sdc", DiskCounters(0, 0)),
            ]
        )
        self.notify_monitor_about_current_disk_stats()

        self.set_disk_counters("sda", DiskCounters(100, 100))
        self.set_disk_counters("sdc", DiskCounters(100, 100))
        self.notify_monitor_about_current_disk_stats()

        observer = mock.Mock()
        self.monitor.add_observer(observer)

        observer.reset_mock()
        self.set_disk_counters("sda", DiskCounters(0, 0))
        self.set_disk_counters("sdc", DiskCounters(0, 0))
        self.notify_monitor_about_current_disk_stats()
        observer.on_disks_added.assert_called_once()
        self.assertCountEqual(
            ["sda", "sdc"], list(observer.on_disks_added.call_args[0][0])
        )
        observer.on_disks_removed.assert_called_once()
        self.assertCountEqual(
            ["sda", "sdc"], list(observer.on_disks_removed.call_args[0][0])
        )


if __name__ == "__main__":
    unittest.main()
