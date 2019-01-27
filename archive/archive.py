"""Provide the Archive class.
"""

from pathlib import Path
import stat
import sys
import tarfile
import tempfile
from archive.manifest import Manifest


class Archive:

    def __init__(self, path, mode='r', paths=None, basedir=None):
        if mode.startswith('r'):
            # FIXME: reading not yet implemented
            raise NotImplementedError
        elif mode.startswith('x'):
            if sys.version_info < (3, 5):
                # The 'x' (exclusive creation) mode was added to
                # tarfile in Python 3.5.
                mode = 'w' + mode[1:]
            self._create(path, mode, paths, basedir)
        else:
            raise ValueError("invalid mode '%s'" % mode)

    def _create(self, path, mode, paths, basedir):
        self.basedir = Path(basedir)
        _paths = []
        if self.basedir.is_absolute():
            raise ValueError("basedir must be relative")
        if len(paths) > 0:
            # We allow two different cases: either
            # - all paths are absolute, or
            # - all paths are relative and start with basedir.
            abspath = None
            for p in paths:
                p = Path(p)
                if abspath is None:
                    abspath = p.is_absolute()
                else:
                    if abspath != p.is_absolute():
                        raise ValueError("mixing of absolute and relative "
                                         "paths is not allowed")
                if not p.is_absolute():
                    # This will raise ValueError if p does not start
                    # with basedir:
                    p.relative_to(self.basedir)
                _paths.append(p)
        else:
            raise ValueError("refusing to create an empty archive")
        self.manifest = Manifest(paths=_paths)
        with tarfile.open(str(path), mode) as tarf:
            with tempfile.TemporaryFile() as tmpf:
                self.manifest.write(tmpf)
                tmpf.seek(0)
                name = str(self.basedir / ".manifest.yaml")
                manifest_info = tarf.gettarinfo(arcname=name, fileobj=tmpf)
                manifest_info.mode = stat.S_IFREG | 0o444
                tarf.addfile(manifest_info, tmpf)
            for fi in self.manifest:
                p = fi.path
                if p.is_absolute():
                    name = str(self.basedir / p.relative_to(p.anchor))
                else:
                    name = str(p)
                tarf.add(str(p), arcname=name, recursive=False)