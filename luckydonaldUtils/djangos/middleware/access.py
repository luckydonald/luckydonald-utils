# -*- coding: utf-8 -*-
__author__ = 'luckydonald'


from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import Http404
from ...logger import logging  # pip install luckydonald-utils
from ...dependencies import import_or_install
logger = logging.getLogger(__name__)

import_or_install("IPy", "IPy")
from IPy import IP  # pip install IPy


class AllowFromIPMiddleware(object):
	"""
	Allow only given IPs to access, else raise a `Http404` error. Is ignoren when `DEBUG` is `True`.
	Checks ranges with https://pypi.python.org/pypi/IPy/ .

	Example:
	The *`settings.py`*
	```
	ALLOW_FROM = ["8.8.8.8", "134.169.0.0/16"]
	```
	Empty array means allow 'all'.

	Mimics the Apache syntax:
	> Allow from 134.169.
	One would write as
	>>> ALLOW_FROM = ["134.169"]
	or
	>>> ALLOW_FROM = ["134.169.0.0/16"]
	in the `settings.py`.
	"""
	buffered_ALLOW_FROM = None

	def process_request(self, request):
		if self.buffered_ALLOW_FROM is None:
			self.buffered_ALLOW_FROM = []
			for ip in settings.ALLOW_FROM:
				self.buffered_ALLOW_FROM.append(IP(ip))
			#end for
		#end if
		if len(self.buffered_ALLOW_FROM) == 0:
			return  # allow
		remote_addr = request.META.get('HTTP_X_REAL_IP', request.META.get('REMOTE_ADDR', None))
		if any([remote_addr in ip for ip in self.buffered_ALLOW_FROM]):
			if settings.DEBUG:
				logger.warn("The IP {remote_addr} should not be allowed, but is served anyway because DEBUG=True.".format(remote_addr=remote_addr))
				return  # allow
			raise Http404  # forbid
			#end if DEBUG
		#end if
	#end def
#end class