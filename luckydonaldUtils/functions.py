from datetime import datetime, timedelta

import functools
import inspect
import logging

from .clazzes import Kwargs

logger = logging.getLogger(__name__)

__author__ = 'luckydonald'
__all__ = [
    "caller", "deprecated", "gone", "cached",
    "CallerResult", "CallerInfo"
]


class CallerResult(Kwargs):
    """
    Contains the data of who called us.

    Can also be used via ** mapping.
    >>> x = CallerResult("aaa", "bbb")
    >>> dict(**x)
    {'self': 'aaa', 'caller': 'bbb'}
    """
    __FIELDS__ = ("self", "caller")

    # noinspection PyMethodParameters
    def __init__(this, self, caller):
        """
        :type  self: CallerInfo
        :type  caller: CallerInfo
        """
        this.self = self
        this.caller = caller
    # end def
# end class


class CallerInfo(Kwargs):
    __FIELDS__ = ("name", "file", "line", "code")

    def __init__(self, name, file, line, code=None):
        self.name = name
        self.file = file
        self.line = line
        self.code = code
    # end def
# end class


def caller(level=0, kwarg_name="call"):
    """
    functions decorated with this will be called with an `call` kwarg, containing information about the function itself, and the caller.
    If the caller could not be fetched correctly, the `caller`s attributes all will be `None`.

    Level is the amount of functions to go upwards. Default is 1.
    kwarg_name is the name of the kwarg parameter we input the caller data as. Default is "call".


    Usage:

    >>> @caller
    ... def whatever(arg, kwarg=None, call=None):
    ...     pass  # do something with the `call` info

    >>> @caller(1)  # change this if you you are deep within another call. You can adust the stack index here.
    ... def whatever(arg, kwarg=None, call=None):
    ...     pass  # do something with the `call` info

    >>> @caller(kwarg_name="_call_info")  # change this if you you are deep within another call. You can adust the stack index here.
    ... def whatever(arg, kwarg=None, _call_info=None):
    ...     pass  # do something with the `_call_info` info
    """
    def caller_func_wrapper(func, level=0, kwarg_name="call"):
        """
        :param func: The function we need to call.

        :param level: The level to go back in stack.
        :type  level: int

        :param kwarg_name: the **kwargs element to write to.
        :type  kwarg_name: str
        :return:
        """

        @functools.wraps(func)
        def caller_wrapping_func(*args, **kwargs):
            # so the decorated function is the 'self' one.
            try:
                self = CallerInfo(
                    name=func.__name__,
                    file=func.__code__.co_filename,
                    line=func.__code__.co_firstlineno + 1,
                )
            except AttributeError as e:
                    logger.debug("self lookup failed", exc_info=True)
                    # we just don't know
                    self = CallerInfo(
                        name=None,
                        file=None,
                        line=None,
                    )
                # end if
            # end try
            try:
                s = inspect.stack()
                # +1 as we need to ignore the caller_wrapping_func
                stack = s[level + 1]  # the +1 out-of-bounds is handled by the except IndexError.
                caller = CallerInfo(
                    name=stack[3],
                    file=stack[1],
                    line=stack[2],
                    code=stack[4][0],
                )
            except (TypeError, IndexError):
                caller = CallerInfo(
                    name=None,
                    file=None,
                    line=None,
                    code=None,
                )
            # end try
            call = CallerResult(
                self=self,
                caller=caller
            )
            kwargs[kwarg_name] = call
            return func(*args, **kwargs)

        return caller_wrapping_func
    # end def

    def caller_wrapping_func_applyer(func):
        return caller_func_wrapper(func, level=level, kwarg_name=kwarg_name)
    # end def

    try:
        is_callable = callable(level)
    except (SyntaxError, NameError):
        is_callable = inspect.isfunction(level) or inspect.isbuiltin(level)
    # end try
    if is_callable:  # level was not provided, level is actually our function to decorate
        func = level
        _func = functools.wraps(func)(caller_func_wrapper)
        return _func(func)  # keeping the defaults at the defaults.
    return caller_wrapping_func_applyer  # else: level is level, we need to return a decorator accepting the function
# end def


def deprecated(func, message=None):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being logged
    when the function is used."""

    if isinstance(func, str):  # @deprecated("message")
        message = func

        def inners(func):  # @deprecated("message")(func)
            return deprecated(func, message)  # @deprecated("message")(func) ->  @deprecated(func, "message")

        return inners

    # end if
    # -> @deprecated(func)

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        try:
            try:  # python 2 + python 3
                f_name = func.__name__
                f_file = func.__code__.co_filename
                f_line = func.__code__.co_firstlineno + 1
            except AttributeError:  # maybe some old python 2?
                f_name = func.func_code.co_name
                f_file = func.func_code.co_filename
                f_line = func.func_code.co_firstlineno + 1
            # end try
            try:
                logger.warning(
                    "Call to deprecated function {f_name} at file {f_file}:{f_line}\n"
                    "{msg}Called from function {c_name} at file {c_file}:{c_line}\nLine: {c_code}".format(
                        f_name=f_name, f_file=f_file,
                        f_line=f_line,
                        msg="Warning: " + message.strip() + "\n" if message else "",
                        c_name=inspect.stack()[1][3], c_file=inspect.stack()[1][1],
                        c_line=inspect.stack()[1][2], c_code=inspect.stack()[1][4][0],
                    ))
            except TypeError:
                logger.warning(
                    "Call to deprecated function {f_name} at file {f_file}:{f_line}{msg}".format(
                        f_name=f_name, f_file=f_file,
                        f_line=f_line, msg="\nWarning: " + message.strip() if message else ""
                    ))
        except (AttributeError, TypeError):
            logger.warning(
                "Call to deprecated function.{msg}".format(msg="\nWarning: " + message.strip() if message else ""),
                exc_info=True
            )
        return func(*args, **kwargs)

    return new_func  # @deprecated(func)


# end def
"""
Test would be
>> @deprecated
>> def foo(): pass

>> @deprecated("Custom Message")
>> def foo(): pass
"""


def gone(func):
    """This is a decorator which can be used to mark functions
    as deprecated, and gone. It will raise a NotImplementedError
    when the function is used."""
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        raise NotImplementedError(
            "Call to deprecated function {} at file {}:{}. Called from function {} at file {}:{}\nLine: {}".format(
                func.__name__, func.__code__.co_filename,  # python2: func.func_code.co_filename
                func.__code__.co_firstlineno + 1,  # python2: func.func_code.co_firstlineno
                inspect.stack()[1][3], inspect.stack()[1][1], inspect.stack()[1][2], inspect.stack()[1][4][0]
            )
        )

    # end def
    return new_func
# end def


def cached(max_age=None):
    """
    Cache a function.
    You can specify a max_age (:class:`datetime.timedelta`) after when the function will be called again.

    :keyword max_age: timedelta of how long we should keep the cache. None means forever.
    :type    max_age: None or timedelta
    """
    # http://stackoverflow.com/a/30698822/3423324
    # _format = {"returns": "I am a return value!!", "max_age": timedelta(seconds=60), "last_hit": datetime.now()}
    memo = {}
    import json

    def stringify(obj):
        if isinstance(obj, (list, tuple)):
            return repr([stringify(x) for x in obj])
        if isinstance(obj, dict):
            res = {}
            for k, v in obj.items():
                res[k] = stringify(k)
            # end for
            return repr(res)
        try:
            return json.dumps(obj)
        except TypeError:
            return str(repr(obj)) + str(obj) + str(id(obj))
            # end if

    def func_wrapper(function, **decorator_kwargs):
        def wrapper(*args, **kwargs):
            args_key = stringify([args, kwargs])
            now = datetime.now()
            if "max_age" in decorator_kwargs:
                max_age_ = decorator_kwargs["max_age"]
            else:
                max_age_ = max_age
            if (args_key) in memo.keys():
                logger.debug(memo[args_key])
                if not max_age_ or now - memo[args_key]["last_hit"] < memo[args_key]["max_age"]:
                    return memo[args_key]["returns"]
                    # end if
            # end if
            res = function(*args, **kwargs)
            memo[args_key] = {"returns": res, "last_hit": now, "max_age": max_age_}
            return res

        return wrapper

    try:
        is_callable = callable(max_age)
    except (SyntaxError, NameError):
        is_callable = inspect.isfunction(max_age) or inspect.isbuiltin(max_age)
    # end try
    if is_callable:  # max_age was not provided, max_age is actually our function to decorate
        func = max_age
        return func_wrapper(func, max_age=None)
    return func_wrapper  # else: max_age is max_age, we need to return a decorator accepting the function
# end def
