"""Provide the Archive class.
"""

from pathlib import Path
import stat
import sys
import tarfile
import tempfile
from archive.manifest import Manifest
from archive.exception import *
from archive.tools import tmp_chdir, checksum

def _is_normalized(p):
    """Check if the path is normalized.
    """
    p = Path.cwd() / p
    if p.resolve() == p:
        return True
    if p.is_symlink():
        return p.resolve().parent == p.parent
    else:
        return False

class Archive:

    def __init__(self):
        self.path = None
        self.basedir = None
        self.manifest = None
        self._file = None

    def create(self, path, compression, paths, basedir=None, workdir=None):
        if sys.version_info < (3, 5):
            # The 'x' (exclusive creation) mode was added to tarfile
            # in Python 3.5.
            mode = 'w:' + compression
        else:
            mode = 'x:' + compression
        if workdir:
            with tmp_chdir(workdir):
                self._create(Path(workdir, path), mode, paths, basedir)
        else:
            self._create(Path(path), mode, paths, basedir)
        return self

    def _create(self, path, mode, paths, basedir):
        self.path = path
        if not paths:
            raise ArchiveCreateError("refusing to create an empty archive")
        if not basedir:
            p = Path(paths[0])
            if p.is_absolute():
                self.basedir = Path(self.path.name.split('.')[0])
            else:
                self.basedir = Path(p.parts[0])
        else:
            self.basedir = Path(basedir)
        if self.basedir.is_absolute():
            raise ArchiveCreateError("basedir must be relative")
        # We allow two different cases: either
        # - all paths are absolute, or
        # - all paths are relative and start with basedir.
        abspath = None
        _paths = []
        for p in paths:
            if not _is_normalized(p):
                raise ArchiveCreateError("invalid path %s: must be normalized" 
                                         % p)
            p = Path(p)
            if abspath is None:
                abspath = p.is_absolute()
            else:
                if abspath != p.is_absolute():
                    raise ArchiveCreateError("mixing of absolute and relative "
                                             "paths is not allowed")
            if not p.is_absolute():
                try:
                    # This will raise ValueError if p does not start
                    # with basedir:
                    p.relative_to(self.basedir)
                except ValueError as e:
                    raise ArchiveCreateError(str(e))
            _paths.append(p)
        if not abspath:
            if self.basedir.is_symlink() or not self.basedir.is_dir():
                raise ArchiveCreateError("basedir must be a directory")
        self.manifest = Manifest(paths=_paths)
        manifest_name = str(self.basedir / ".manifest.yaml")
        with tarfile.open(str(self.path), mode) as tarf:
            with tempfile.TemporaryFile() as tmpf:
                self.manifest.write(tmpf)
                tmpf.seek(0)
                manifest_info = tarf.gettarinfo(arcname=manifest_name, 
                                                fileobj=tmpf)
                manifest_info.mode = stat.S_IFREG | 0o444
                tarf.addfile(manifest_info, tmpf)
            for fi in self.manifest:
                p = fi.path
                name = self._arcname(p)
                if name == manifest_name:
                    raise ArchiveCreateError("cannot add %s: "
                                             "this filename is reserved" % p)
                tarf.add(str(p), arcname=name, recursive=False)

    def open(self, path):
        self.path = Path(path)
        self._open()
        ti = self._file.next()
        path = Path(ti.path)
        if path.name != ".manifest.yaml":
            raise ArchiveIntegrityError("manifest not found")
        self.basedir = path.parent
        self.manifest = Manifest(fileobj=self._file.extractfile(ti))
        return self

    def _open(self):
        try:
            self._file = tarfile.open(str(self.path), 'r')
        except OSError as e:
            raise ArchiveReadError(str(e))

    def close(self):
        if self._file:
            self._file.close()
        self._file = None

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.close()

    def __del__(self):
        self.close()

    def _arcname(self, p):
        if p.is_absolute():
            return str(self.basedir / p.relative_to(p.root))
        else:
            return str(p)

    def verify(self):
        if not self._file:
            raise ValueError("archive is closed.")
        for fileinfo in self.manifest:
            self._verify_item(fileinfo)

    def _verify_item(self, fileinfo):

        def _check_condition(cond, item, message):
            if not cond:
                raise ArchiveIntegrityError("%s: %s" % (item, message))

        itemname = "%s:%s" % (self.path, fileinfo.path)
        try:
            tarinfo = self._file.getmember(self._arcname(fileinfo.path))
        except KeyError:
            raise ArchiveIntegrityError("%s: missing" % itemname)
        _check_condition(tarinfo.mode == fileinfo.mode,
                         itemname, "wrong mode")
        _check_condition(int(tarinfo.mtime) == int(fileinfo.mtime),
                         itemname, "wrong modification time")
        if fileinfo.is_dir():
            _check_condition(tarinfo.isdir(),
                             itemname, "wrong type, expected directory")
        elif fileinfo.is_file():
            _check_condition(tarinfo.isfile(),
                             itemname, "wrong type, expected regular file")
            _check_condition(tarinfo.size == fileinfo.size,
                             itemname, "wrong size")
            with self._file.extractfile(tarinfo) as f:
                cs = checksum(f, fileinfo.checksum.keys())
                _check_condition(cs == fileinfo.checksum,
                                 itemname, "checksum does not match")
        elif fileinfo.is_symlink():
            _check_condition(tarinfo.issym(),
                             itemname, "wrong type, expected symbolic link")
            _check_condition(tarinfo.linkname == str(fileinfo.target),
                             itemname, "wrong link target")
        else:
            raise ArchiveIntegrityError("%s: invalid type" % (itemname))
