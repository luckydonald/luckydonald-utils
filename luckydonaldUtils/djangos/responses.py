# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

from luckydonaldUtils.logger import logging  # pip install luckydonald-utils
logger = logging.getLogger(__name__)
from django.http import JsonResponse
from django.conf import settings

def json_response(content=None, status=None, statusText=None, exception=None):
	msg = {"status": 200, "statusText": "OK", "content": None}
	if isinstance(exception, Exception):
		logger.warn("Json Exception", exc_info=True)
		msg["status"] = 500
		msg["statusText"] = "INTERNAL SERVER ERROR"
		msg["content"] = "Generic Error"
		if settings.DEBUG:
			msg["exception"] = str(exception)
		#end if
	#end if
	if status:
		msg["status"] = int(status)
	if statusText:
		msg["statusText"] = statusText
	if content:
		msg["content"] = content
	#end if
	return JsonResponse(msg, status=msg["status"])