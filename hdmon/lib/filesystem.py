from pathlib import Path
from typing import Generator
import glob


def find(
    pattern: str, *, recursive=True, follow_symlinks=True, strict=True
) -> Generator[Path, None, None]:
    for path_string in glob.glob(pattern, recursive=recursive):
        path = Path(path_string)
        if follow_symlinks:
            path = path.resolve(strict=strict)
        yield path
