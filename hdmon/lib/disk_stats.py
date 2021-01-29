from dataclasses import dataclass


_PATH = "/proc/diskstats"


@dataclass(frozen=True)
class DiskStat:
    device_name: str
    sectors_read: int
    sectors_written: int


def iter_disk_stats():
    with open(_PATH) as fh:
        for line in fh:
            parts = line.split()
            yield DiskStat(
                device_name=parts[2],
                sectors_read=int(parts[5]),
                sectors_written=int(parts[9]),
            )
