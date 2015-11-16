# -*- coding: utf-8 -*-
from luckydonaldUtils.decorators import decorator_with_default_params

__author__ = 'luckydonald'

from ..logger import logging  # pip install luckydonald-utils
logger = logging.getLogger(__name__)
from ..encoding import to_unicode

from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.utils.decorators import available_attrs
from functools import wraps

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


def catch_exception(*d_args, **d_kwargs):
	""" View decorator that allows to render specified Exception Types.
	# You can specify a `exception_render_func` which will be called with the exception as argument.

		Example:
		 @catch_exception(django.http.Http404)
			def view(request, ...):
 		 		...

		For class-based views use:
		@method_decorator(catch_exception(django.http.Http404))
		 def get(self, request, ...)
 			...

		>>> # example
		>>> from luckydonaldUtils.djangos.responses import catch_exception
		>>> def lol(e):
		... 	return HttpResponse("ERROR " + str(e) + " YEAH!") # but no status=500

		>>> @catch_exception(AttributeError)
		... @catch_exception(ValueError, exception_render_func=lol)
		... def foobar(do_fail = 0):
		... 	if do_fail == 1:
		... 		raise AttributeError("ololol! Without custom renderer")
		... 	elif do_fail == 2:
		... 		raise ValueError("hua! With custom renderer.")
		... 	elif do_fail == 3:
		... 		raise AssertionError("Another test Error, not handled.")
		... 	return HttpResponse("normal output")


	"""

	def decorator(func, exception, exception_render_func=None):
		@wraps(func, assigned=available_attrs(func))
		def inner(request, *args, **kwargs):
			try:
				response = func(request, *args, **kwargs)
			except exception as e:
				logger.debug("Discarding response, because expected Exception occured. {err_str}".format(err_str=str(e)))
				if exception_render_func:
					return exception_render_func(e)
				return HttpResponse(str(e), status=500)
			#end try
			return response
		return inner
	return decorator_with_default_params(decorator, d_args, d_kwargs, [DoOutputException], {"exception_render_func": None})

class DoOutputException(Exception):
	pass