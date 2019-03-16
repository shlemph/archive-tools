"""pytest configuration.
"""

from pathlib import Path
import shutil
import tempfile
import pytest


_cleanup = True
testdir = Path(__file__).parent

def pytest_addoption(parser):
    parser.addoption("--no-cleanup", action="store_true", default=False,
                     help="do not clean up temporary data after the test.")

def pytest_configure(config):
    global _cleanup
    _cleanup = not config.getoption("--no-cleanup")

def gettestdata(fname):
    path = testdir / "data" / fname
    assert path.is_file()
    return path

def _get_checksums():
    checksums_file = testdir / "data" / ".sha256"
    checksums = dict()
    with checksums_file.open("rt") as f:
        while True:
            l = f.readline()
            if not l:
                break
            cs, fp = l.split()
            checksums[fp] = cs
    return checksums

checksums = _get_checksums()

class TmpDir(object):
    """Provide a temporary directory.
    """
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="archive-tools-test-"))
    def cleanup(self):
        if self.dir and _cleanup:
            shutil.rmtree(str(self.dir))
        self.dir = None
    def __enter__(self):
        return self.dir
    def __exit__(self, type, value, tb):
        self.cleanup()
    def __del__(self):
        self.cleanup()

@pytest.fixture(scope="module")
def tmpdir(request):
    with TmpDir() as td:
        yield td

@pytest.fixture(scope="function")
def archive_name(request):
    return "archive-%s.tar" % request.function.__name__

def setup_testdata(main_dir, dirs=[], files=[], symlinks=[]):
    for d, m in dirs:
        p = main_dir / d
        p.mkdir(parents=True)
        p.chmod(m)
    for f, m in files:
        p = main_dir / f
        shutil.copy(str(gettestdata(f.name)), str(p))
        p.chmod(m)
    for f, t in symlinks:
        p = main_dir / f
        p.symlink_to(t)

def check_manifest(manifest, prefix_dir=None, dirs=[], files=[], symlinks=[]):
    assert len(manifest) == len(dirs) + len(files) + len(symlinks)
    for p, m in dirs:
        if prefix_dir:
            p = prefix_dir / p
        fi = manifest.find(p)
        assert fi
        assert fi.type == 'd'
        assert fi.path == p
        assert fi.mode == m
    for p, m in files:
        if prefix_dir:
            p = prefix_dir / p
        fi = manifest.find(p)
        assert fi
        assert fi.type == 'f'
        assert fi.path == p
        assert fi.mode == m
        assert fi.checksum['sha256'] == checksums[p.name]
    for p, t in symlinks:
        if prefix_dir:
            p = prefix_dir / p
        fi = manifest.find(p)
        assert fi
        assert fi.type == 'l'
        assert fi.path == p
        assert fi.target == t
