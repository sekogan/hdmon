#!/usr/bin/env python3

import os
import shutil

from .lib.logger import LOGGER as logger, log_current_exception
from .service import CONFIG_PATH


SYSTEMD_UNIT_FILE_PATH = "/usr/lib/systemd/system/hdmon.service"

SYSTEMD_UNIT_FILE_CONTENT = """\
[Unit]
Description=Hard Disk Monitor

[Service]
ExecStart={hdmon}
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

  once_idle:
    # Runs a command if a disk is idle for specified amount of time.
    delay: 2h
    run: /usr/sbin/hdparm -y $disk_path
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


def delete_file_if_exists(path):
    logger.info('Removing "%s"...', path)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    logger.info("Done")


def install():
    try:
        create_file_if_not_exists(CONFIG_PATH, DEFAULT_CONFIG)

        hdmon_path = shutil.which("hdmon")
        unit_file_content = SYSTEMD_UNIT_FILE_CONTENT.format(hdmon=hdmon_path)
        create_file_if_not_exists(SYSTEMD_UNIT_FILE_PATH, unit_file_content)
        return 0
    except Exception:
        log_current_exception()
        return 1


def uninstall():
    try:
        delete_file_if_exists(SYSTEMD_UNIT_FILE_PATH)
        return 0
    except Exception:
        log_current_exception()
        return 1
