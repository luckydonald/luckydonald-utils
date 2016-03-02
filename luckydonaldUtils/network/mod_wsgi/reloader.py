# -*- coding: utf-8 -*-
# https://code.google.com/p/modwsgi/wiki/ReloadingSourceCode
"""
Add auto reloading capabilities.

Use in your wsgi file like this:

>>> import os
>>>
>>> from luckydonaldUtils.network.mod_wsgi import reloader
>>> reloader.start(interval=1.0)
>>> reloader.track(os.path.join(os.path.dirname(__file__), 'site.cf'))
>>>
>>> def application(environ, start_response):
>>>    ...

"""

from __future__ import print_function

__author__ = 'luckydonald'

from luckydonaldUtils.logger import logging  # pip install luckydonald-utils

logger = logging.getLogger(__name__)

import os
import sys
import signal
import threading
import atexit

try:
    from queue import Queue  # py3
except ImportError:
    from Queue import Queue  # py2
# end try

_interval = 1.0
_times = {}
_files = []

_running = False
_queue = Queue()
_lock = threading.Lock()


def warning(*objs):
    print(*objs, file=sys.stderr)


def _restart(path):
    _queue.put(True)
    prefix = 'monitor (pid=%d):' % os.getpid()
    warning('%s Change detected to \'%s\'.' % (prefix, path))
    warning('%s Triggering process restart.' % prefix)
    os.kill(os.getpid(), signal.SIGINT)


def _modified(path):
    try:
        # If path doesn't denote a file and were previously
        # tracking it, then it has been removed or the file type
        # has changed so force a restart. If not previously
        # tracking the file then we can ignore it as probably
        # pseudo reference such as when file extracted from a
        # collection of modules contained in a zip file.

        if not os.path.isfile(path):
            return path in _times

        # Check for when file last modified.

        mtime = os.stat(path).st_mtime
        if path not in _times:
            _times[path] = mtime

        # Force restart when modification time has changed, even
        # if time now older, as that could indicate older file
        # has been restored.

        if mtime != _times[path]:
            return True
    except:
        # If any exception occured, likely that file has been
        # been removed just before stat(), so force a restart.

        return True

    return False


def _monitor():
    while 1:
        # Check modification times on all files in sys.modules.

        for module in sys.modules.values():
            if not hasattr(module, '__file__'):
                continue
            path = getattr(module, '__file__')
            if not path:
                continue
            if os.path.splitext(path)[1] in ['.pyc', '.pyo', '.pyd']:
                path = path[:-1]
            if _modified(path):
                return _restart(path)

        # Check modification times on files which have
        # specifically been registered for monitoring.

        for path in _files:
            if _modified(path):
                return _restart(path)

        # Go to sleep for specified interval.

        try:
            return _queue.get(timeout=_interval)
        except:
            pass


_thread = threading.Thread(target=_monitor)
_thread.setDaemon(True)


def _exiting():
    try:
        _queue.put(True)
    except:
        pass
    _thread.join()


atexit.register(_exiting)


def track(path):
    if not path in _files:
        _files.append(path)


def start(interval=1.0):
    global _interval
    if interval < _interval:
        _interval = interval

    global _running
    _lock.acquire()
    if not _running:
        prefix = 'monitor (pid=%d):' % os.getpid()
        warning(sys.stderr, '%s Starting change monitor.' % prefix)
        _running = True
        _thread.start()
    _lock.release()
