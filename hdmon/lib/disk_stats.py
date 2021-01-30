from dataclasses import dataclass
from typing import Generator, Tuple


_PATH = "/proc/diskstats"


@dataclass(frozen=True)
class DiskCounters:
    sectors_read: int
    sectors_written: int


DeviceNameAndCounters = Tuple[str, DiskCounters]


def iter_disk_stats() -> Generator[DeviceNameAndCounters, None, None]:
    with open(_PATH) as fh:
        for line in fh:
            parts = line.split()
            device_name = parts[2]
            counters = DiskCounters(
                sectors_read=int(parts[5]),
                sectors_written=int(parts[9]),
            )
            yield (device_name, counters)
