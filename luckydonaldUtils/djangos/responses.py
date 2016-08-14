# -*- coding: utf-8 -*-
try:
    from django.http import JsonResponse, HttpResponse
    from django.conf import settings
    from django.utils.decorators import available_attrs
except ImportError:  # pragma nocover
    from ..dependencies import import_or_install

    available_attrs = import_or_install("django.utils.decorators.available_attrs", "django")
    JsonResponse = import_or_install("django.http.JsonResponse", "django")
    HttpResponse = import_or_install("django.http.HttpResponse", "django")
    settings = import_or_install("django.conf.settings", "django")
# end try
from functools import wraps
from ..logger import logging  # pip install luckydonald-utils

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)


def json_response(content=None, status=None, statusText=None, exception=None):
    msg = {"status": 200, "statusText": "OK", "content": None}
    if isinstance(exception, Exception):
        logger.warn("Json Exception", exc_info=True)
        msg["status"] = 500
        msg["statusText"] = "INTERNAL SERVER ERROR"
        msg["content"] = "Generic Error"
        if settings.DEBUG:
            msg["exception"] = str(exception)
            # end if
    # end if
    if status:
        msg["status"] = int(status)
    if statusText:
        msg["statusText"] = statusText
    if content:
        msg["content"] = content
    # end if
    return JsonResponse(msg, status=msg["status"])


####
#
#  Render Exceptions
#
####

def render_all_exceptions(function):
    """
    View decorator that renders Exception in django.
    If you want to catch and respond specific Exception types, see `render_specific_exception` decorator

    >>> @render_all_exceptions
    ... def foobar()
    ... 	pass # code goes here

    """

    @wraps(function, assigned=available_attrs(function))
    def function_callable(request, *args, **kwargs):
        try:
            response = function(request, *args, **kwargs)
        except Exception as e:
            logger.debug("Exception response, because expected Exception occurred. {err_str}".format(err_str=str(e)))
            return HttpResponse(str(e), status=500)
        # end try
        return response

    return function_callable


def render_DoOutputException(function):
    """
    View decorator that renders DoOutputException's message in django.
    If you want to catch and respond specific Exception types, see `render_specific_exception` decorator.
    If you want to catch and display all Exception types, see `render_all_exceptions` decorator

    >>> @render_DoOutputException
    ... def foobar()
    ... 	raise ValueError("lol.")

    """

    @wraps(function, assigned=available_attrs(function))
    def function_callable(request, *args, **kwargs):
        try:
            response = function(request, *args, **kwargs)
        except DoOutputException as e:
            logger.debug(
                "Exception response, because expected DoOutputException occurred. {err_str}".format(err_str=str(e)))
            return HttpResponse(str(e), status=500)
        # end try
        return response

    return function_callable


def render_specific_exception(exception_class, exception_render_func=None):
    """
     View decorator that allows to render specified Exception Types.
    You can specify a `exception_render_func` which will be called with the request and the exception as arguments.

    :param   exception: The Exception you want to be catched and rendered as response.
    :type    exception: class (inherits Exception)

    :keyword exception_render_func: an optional function to render the exception. It will be called with `func(request, e)`
    :type    exception_render_func: function (2 parameters [request, exception])

    :return: Django Response
    :rtype : HttpResponse




    Example:
     @render_specific_exception(django.http.Http404)
        def view(request, ...):
            ...

    For class-based views use:
    @method_decorator(render_specific_exception(django.http.Http404))
     def get(self, request, ...)
        ...

    Import it
    >>> from luckydonaldUtils.djangos import render_specific_exception


    How to use
    >>> @render_specific_exception(AttributeError)
    ... @render_specific_exception(ValueError, exception_render_func=foo_error_renderer)  # foo_error_renderer see below.
    ... def django_foo(do_fail = 0):
    ... 	if do_fail == 1:
    ... 		raise AttributeError("ololol! Without custom renderer")
    ... 	elif do_fail == 2:
    ... 		raise ValueError("hua! With custom renderer.")
    ... 	elif do_fail == 3:
    ... 		raise AssertionError("Another test Error, not handled.")
    ... 	return HttpResponse("normal output")

    Example exception_render_func function
    >>> def foo_error_renderer(request, e):
    ... 	return HttpResponse("ERROR " + str(e) + " YEAH!") # but no status=500

    Try it:
    >>> django_foo(0)
    >>> django_foo(1)
    >>> django_foo(2)
    >>> django_foo(3)
    """

    def create_function(function):
        @wraps(function, assigned=available_attrs(function))
        def function_callable(request, *args, **kwargs):
            try:
                response = function(request, *args, **kwargs)
            except exception_class as e:
                logger.debug(
                    "Exception response, because expected Exception occurred. {err_str}".format(err_str=str(e)))
                if exception_render_func:
                    return exception_render_func(request, e)
                return HttpResponse(str(e), status=500)
            # end try
            return response

        return function_callable

    return create_function


class DoOutputException(Exception):
    pass
