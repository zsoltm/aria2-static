from contextlib import contextmanager
import tempfile
import shutil
import os
import logging

__log = logging.getLogger(__name__)


@contextmanager
def work_dir(cwd=True):
    name = tempfile.mkdtemp()
    old_cwd = os.getcwd() if cwd else None
    __log.debug("created temporary dir %s" % name)
    try:
        if cwd:
            os.chdir(name)
        yield name
    finally:
        if old_cwd:
            os.chdir(old_cwd)
        __log.debug("removed temporary dir %s" % name)
        shutil.rmtree(name)
