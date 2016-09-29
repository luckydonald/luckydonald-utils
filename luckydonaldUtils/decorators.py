# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging  # pip install luckydonald-utils

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)

from .functions import *  # because everyone searches for the decorators in this file ... lel.

#TODO: py2 safe?

def decorator_with_default_params(real_decorator, args, kwargs, default_args=None, default_kwargs=None):
    """
    This function makes it easy to build a parameterized decorator, having a default value.
    Construct your decorator like this:

    >>> def decorator(*d_args, **d_kwargs): # d_args with d like decorator
    ... 	def function_processor(function, *args, **kwargs):
    ... 		print("additional_args", args, kwargs)
    ... 		# just do stuff here with the function, or with the args.
    ... 		return function
    ... 	return decorator_with_default_params(function_processor, d_args, d_kwargs, default_args=["I am a default argument, used if you don't provide args"])

    so you can use that decorator:

    >>> @decorator # will fall back to the default value.
    ... @decorator("hey") # with parameter(s).
    ... @decorator(key="value") # with parameter(s).
    ... def foobar()
    ... 	pass
    ... foobar = decorator(foobar) # use default value # same as @decorator
    ... foobar = decorator(foobar, "hey") # with parameter(s) # same as @decorator("hey")
    ... foobar = decorator(foobar, key="value") # with parameter(s) # same as @decorator(key="value")

    :param real_decorator: The function whitch gets a function, and *args. Must return the function again.
    :param default_args_list: arguments which will be provided to the real_decorator, if @decorator is used without params
    :param args:
    :param kwargs:
    :return:
    """
    if default_args is None:
        default_args = []
    if default_kwargs is None:
        default_kwargs = {}
    if args is not None and len(args) > 0 and callable(args[0]):
        func = args[0]
        if len(args) == 1:  # @admin  or  func = admin(func)
            if kwargs is None or len(kwargs) == 0: # no arguments/kwargs
                return real_decorator(func, *default_args, **default_kwargs)  # func = arg[0]
            else:  # has kwargs
                return real_decorator(*args, **kwargs) # args contains func.
        else:  # test = admin(test, param)
            return real_decorator(*args, **kwargs)
    else:  # @admin(param)
        if args is None or len(args) == 0: # you don't provide a function at all.
            if kwargs is None or len(kwargs) == 0:
                args = default_args
                kwargs = default_kwargs
        elif args[0] == Ellipsis: # so you can insert callables, after Ellipsis as first argument.
            args = args[1:]
        def real_decorator_param_provider(func):
            return real_decorator(func, *args, **kwargs)
        return real_decorator_param_provider  # it will call real_decorator(func) by its own

# end def
