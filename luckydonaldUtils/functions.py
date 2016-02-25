import functools
import inspect
from DictObject import DictObject
import logging
logger = logging.getLogger(__name__)

__author__ = 'luckydonald'


def caller(func):
    """
    functions decorated with this will be called with an `call` kwarg, containing information about the function itself, and the caller.
    If the caller could not be fetched correctly, the `caller`s attributes all will be `None`.
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        try:
            stack = inspect.stack()[1]
            call = {"self": {"name": func.__name__, "file": func.__code__.co_filename,
                             "line": func.__code__.co_firstlineno + 1},
                    "caller": {"name": stack[3], "file": stack[1], "line": stack[2], "code": stack[4][0]}
                    }
        except TypeError:
            call = {"self": {"name": func.__name__, "file": func.__code__.co_filename,
                             "line": func.__code__.co_firstlineno + 1},
                    "caller": {"name": None, "file": None, "line": None, "code": None}
                    }
        kwargs["call"] = call
        return func(*args, **kwargs)

    return new_func


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being logged
    when the function is used."""

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        try:
            logger.warn(
                "Call to deprecated function {} at file {}:{}. Called from function {} at file {}:{}\nLine: {}".format(
                    func.__name__, func.__code__.co_filename,  # python2: func.func_code.co_filename
                    func.__code__.co_firstlineno + 1,  # python2: func.func_code.co_firstlineno
                    inspect.stack()[1][3], inspect.stack()[1][1], inspect.stack()[1][2], inspect.stack()[1][4][0],
                ))
        except TypeError:
            logger.warn(
                "Call to deprecated function {} at file {}:{}.".format(func.__name__, func.__code__.co_filename,
                                                                       func.__code__.co_firstlineno + 1))
        return func(*args, **kwargs)

    return new_func


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
            ))

    return new_func
