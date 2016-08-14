# -*- coding: utf-8 -*-

import sys
from ..dependencies import import_or_install
from ..logger import logging
import datetime as datetime

try:
    from pytz import timezone
except ImportError:  # pragma nocover
    timezone = import_or_install("pytz.timezone", "pytz")
# end try

__author__ = 'luckydonald'
__all__ = ["get_local_time", "loop_seconds_between_times"]

logger = logging.getLogger(__name__)

if sys.version < "3":
    def get_local_time(time, time_zone):
        return _get_local_time(time, time_zone)


    def loop_seconds_between_times(datetime1, datetime2):
        return _loop_seconds_between_times(datetime1, datetime2)
else:
    from .py3 import get_local_time, loop_seconds_between_times
# end if


def _get_local_time(time, time_zone):
    if time_zone is None:
        time_zone = "Europe/Berlin"  # todo: config
    return timezone('UTC').localize(time).astimezone(timezone(time_zone))


def _loop_seconds_between_times(datetime1, datetime2):
    delta = datetime2 - datetime1
    seconds = delta.total_seconds()
    for x in range(0, int(seconds)):
        yield (datetime1 + datetime.timedelta(seconds=x))
    yield datetime2  # so loop_seconds_between_times(dat,dat) is at least called once with dat.
