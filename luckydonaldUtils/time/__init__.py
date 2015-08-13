# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

from luckydonaldUtils.logging import logging  # pip install luckydonald-utils
logger = logging.getLogger(__name__)


# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

from luckydonaldUtils.Logging import logging
from ..dependencies import import_or_install

logger = logging.getLogger(__name__)

import datetime as datetime
import_or_install("pytz", "pytz")
from pytz import timezone

__all__ = ["get_local_time", "loop_seconds_between_times"]


def get_local_time(time, time_zone):
	if time_zone is None:
		time_zone = "Europe/Berlin" # todo: config
	return timezone('UTC').localize(time).astimezone(timezone(time_zone))


def loop_seconds_between_times(datetime1, datetime2):
	delta = datetime2 - datetime1
	seconds = delta.total_seconds()
	for x in range(0, int(seconds)):
		yield (datetime1 + datetime.timedelta(seconds=x))
	yield datetime2  # so loop_seconds_between_times(dat,dat) is at least called once with dat.

