# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

from ...eastereggs.headers import get_headers as get_easteregg_headers
from ...logger import logging  # pip install luckydonald-utils
logger = logging.getLogger(__name__)

class EastereggHeadersMiddleware(object):
	"""
	Sets some funny headers.

	Include in your `MIDDLEWARE_CLASSES: "luckydonaldUtils.djangos.middleware.headers.EastereggHeadersMiddleware"
	"""
	def process_request(self, response):
		for header_key, header_value in get_easteregg_headers().items():
			try:
				if not isinstance(header_value, str):
					raise TypeError("Keyword-parameter '{param}' is not type str but {type}, and str() failed.".format(param=header_key, type=type(header_value)))
				if isinstance(header_value, str):
					response[header_key.replace("_","-")] = header_value
				else:
					raise TypeError("Keyword-parameter '{param}' is not type str but {type}.".format(param=header_key, type=type(header_value)))
			except TypeError:
				logger.exception("Header error")
				continue
			# end try
			return response

	pass