import functools
import inspect
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
