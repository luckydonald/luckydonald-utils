# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

""" Python 3 only """

def success(self, msg, *args, exc_info=False, **kwargs):
	"""
	Log 'msg % args' with severity 'SUCCESS'.

	To pass exception information, use the keyword argument exc_info with
	a true value.

	logger.debug("Houston, we landed in the %s", "moon", exc_info=False)
	"""
	kwargs["exc_info"] = exc_info
	self._success(msg, *args, **kwargs)