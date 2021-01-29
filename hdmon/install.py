#!/usr/bin/env python3

import os

from .lib.logger import LOGGER as logger
from .main import CONFIG_LOCATIONS


SYSTEMD_UNIT_FILE_PATH = "/etc/systemd/system/hdmon.service"

SYSTEMD_UNIT_FILE_CONTENT = """\
[Unit]
Description=Hard Disk Monitor

[Service]
ExecStart=/usr/bin/hdmon
Restart=always

[Install]
WantedBy=default.target
"""

DEFAULT_CONFIG = """\
# Hard Disk Monitor configuration

# Each profile define a set of disks and rules that apply to them
profiles:

- disks:
    # Add your disks here. Should be absolute paths or patterns.
    # Patterns can contain "*", "**" and "?".
    #
    # Examples:
    # - /dev/sd?
    # - /dev/disk/by-label/label

  spin_down:
    # This section defines when and how spin down idle disks
    when: idle
    options:
      delay: 2h
    command: /usr/sbin/hdparm -y $disk_path
"""


def create_file_if_not_exists(path, content, mode=0o644):
    if os.path.exists(path):
        logger.warning('File "%s" already exists, nothing to do', path)
        return 0

    logger.info('Creating "%s"...', path)
    with open(path, "x") as fh:
        fh.write(content)
    logger.info("Doing chmod...")
    os.chmod(path, mode)
    logger.info("Done")


def main():
    try:
        create_file_if_not_exists(CONFIG_LOCATIONS[0], DEFAULT_CONFIG)
        create_file_if_not_exists(SYSTEMD_UNIT_FILE_PATH, SYSTEMD_UNIT_FILE_CONTENT)
        return 0
    except Exception as error:
        logger.error("%s", error)
        return 1


if __name__ == "__main__":
    exit(main())
