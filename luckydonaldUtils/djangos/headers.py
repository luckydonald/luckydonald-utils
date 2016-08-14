# -*- coding: utf-8 -*-
from functools import wraps

try:
    from django.utils.decorators import available_attrs
except ImportError:  # pragma nocover
    from ..dependencies import import_or_install

    available_attrs = import_or_install("django.utils.decorators.available_attrs", "django")
# end try

from ..eastereggs.headers import get_headers  as get_easteregg_headers

__author__ = 'luckydonald'


def headers(*headers_as_dict, **headers_as_kwargs):
    """Decorator adding arbitrary HTTP headers to the response.

    This decorator adds HTTP headers specified in the argument (map), to the
    HTTPResponse returned by the function being decorated.

    Example:

    >>> @headers({'Refresh': '10', 'X-Bender': 'Bite my shiny, metal ass!'})
    >>> @headers(Refresh='10', X_Bender='Bite my shiny, metal ass!')
    >>> def index(request):
    >>> 	pass  # your stuff.

    Modified from https://djangosnippets.org/snippets/275/
    """

    def headers_wrapper(fun):
        @wraps(fun, assigned=available_attrs(fun))
        def wrapped_function(*args, **kwargs):
            response = fun(*args, **kwargs)
            for arg in headers_as_dict:
                if isinstance(arg, dict):
                    for k, v in headers_as_kwargs.items():
                        response[k] = v
                else:
                    raise TypeError("Parameter is not type dict but {}".format(type(arg)))
            for kwarg_key, kwarg_value in headers_as_kwargs.items():
                if not isinstance(kwarg_value, str):
                    # try:
                    #	temp = str(kwarg_value)
                    #	kwarg_value = temp
					# except:
                    raise TypeError("Keyword-parameter '{param}' is not type str but {type}, and str() failed.".format(
                        param=kwarg_key, type=type(kwarg_value)))
                if isinstance(kwarg_value, str):
                    response[kwarg_key.replace("_", "-")] = kwarg_value
                else:
                    raise TypeError("Keyword-parameter '{param}' is not type str but {type}.".format(param=kwarg_key,
                                                                                                     type=type(
                                                                                                         kwarg_value)))
            return response

        return wrapped_function

    return headers_wrapper


def header(name, value):
    # View decorator that sets a response header.
    #
    # Example:
    # @header('X-Powered-By', 'Django')
    # def view(request, ...):
    #     ....
    #
    # For class-based views use:
    # @method_decorator(header('X-Powered-By', 'Django'))
    # def get(self, request, ...)
    #     ...
    #
    # Taken from https://djangosnippets.org/snippets/2895/
    def decorator(func):
        @wraps(func, assigned=available_attrs(func))
        def inner(request, *args, **kwargs):
            response = func(request, *args, **kwargs)
            response[name] = value
            return response

        return inner

    return decorator


def easteregg_headers(func):
    return headers(get_easteregg_headers())(func)
