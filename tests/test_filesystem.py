import os
from pathlib import Path
import tempfile
import unittest

import hdmon.lib.filesystem


class FileSystemLibTestCase(unittest.TestCase):
    def test_find(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            dev = Path("dev")
            dev.mkdir()
            (dev / "sda").touch()
            (dev / "sdb").touch()
            (dev / "sdc").touch()
            by_label = dev / "disk" / "by-label"
            by_label.mkdir(parents=True)
            relative_dev = Path("..") / ".."
            (by_label / "test1").symlink_to(relative_dev / "sda")
            (by_label / "test2").symlink_to(relative_dev / "sdb")
            (by_label / "test3").symlink_to(relative_dev / "sdc")

            paths = list(
                str(path.relative_to(temp_dir))
                for path in hdmon.lib.filesystem.find("dev/disk/by-label/*")
            )
            self.assertCountEqual(["dev/sda", "dev/sdb", "dev/sdc"], paths)

            paths = list(
                str(path.relative_to(temp_dir))
                for path in hdmon.lib.filesystem.find("dev/disk/**")
                if not path.is_dir()
            )
            self.assertCountEqual(["dev/sda", "dev/sdb", "dev/sdc"], paths)

            paths = list(
                str(path.relative_to(temp_dir))
                for path in hdmon.lib.filesystem.find("dev/*")
                if not path.is_dir()
            )
            self.assertCountEqual(["dev/sda", "dev/sdb", "dev/sdc"], paths)

            paths = list(
                str(path.relative_to(temp_dir))
                for path in hdmon.lib.filesystem.find("dev/sda")
            )
            self.assertCountEqual(["dev/sda"], paths)
