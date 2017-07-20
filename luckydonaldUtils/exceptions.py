# -*- coding: utf-8 -*-

import logging
import warnings

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)


def assert_type_or_raise(value, expected_type_clazz_or_tuple, *more_clazzes, exception_clazz=TypeError,
                         parameter_name=None):
    """
    A better `assert(isinstance(a, B)` because it supports `None` (as well as some other types except tuple or list), and an nice exception text.

    :param value: The variable to check
    :param expected_type_clazz_or_tuple: a class or value  or  list/tuple of that
    :param *more_clazzes: even more classes or values
    :param exception_clazz: type of the exception raised. Defaults to :class:`TypeError`
    :param parameter_name: setting will add information that given parameter was wrong, instead of just saying "Should be type"  

    :raises: exception_clazz
    :return: Nothing


    Examples/Tests:

    Check if None:

        >>> val = None
        >>> assert_type_or_raise(val, None)

        >>> assert_type_or_raise(val, [None])

    Check multible:

        >>> assert_type_or_raise(val, [None, bool, int])

        >>> assert_type_or_raise(val, (None, bool, int))

        >>> assert_type_or_raise(val, None, bool, int)

        >>> assert_type_or_raise(val, [None, bool], int)

        >>> assert_type_or_raise(val, None, [bool, int])

        >>> assert_type_or_raise(1, [None, bool, int])

        >>> assert_type_or_raise(True, [None, bool, int])

        >>> assert_type_or_raise(1, [None, bool, 1])

        >>> assert_type_or_raise(True, [None, True, int])
        
        >>> assert_type_or_raise("lel", [None, True, int, "lel"])
        
        >>> assert_type_or_raise(True, [None, True, int, "lel"])
        
        >>> assert_type_or_raise(True, [None, True, int, "lel"], exception_clazz=ValueError)
        
        >>> assert_type_or_raise(True, [None, True, int, "lel"], parameter_name="foobar")
        

    Failing asserts:

        >>> assert_type_or_raise("True", [None, True, int])
        Traceback (most recent call last):
        ...
        TypeError: Should be one of the types [None, True, <class 'int'>], but is type <class 'str'>: 'True'

        >>> assert_type_or_raise(None, [True, int])
        Traceback (most recent call last):
        ...
        TypeError: Should be one of the types [True, <class 'int'>], but is type <class 'NoneType'>: None


        >>> assert_type_or_raise("lelz", [None, True, int, "lel"])
        Traceback (most recent call last):
        ...
        TypeError: Should be one of the types [None, True, <class 'int'>, 'lel'], but is type <class 'str'>: 'lelz'


    Custom Exception Type:

        >>> assert_type_or_raise(None, [True, int], exception_clazz=ValueError)
        Traceback (most recent call last):
        ...
        ValueError: Should be one of the types [True, <class 'int'>], but is type <class 'NoneType'>: None


    Parameter name supplied:
        
        >>> assert_type_or_raise(None, [True, int], parameter_name="foobar")
        Traceback (most recent call last):
        ...
        TypeError: The parameter foobar should be one of the types [True, <class 'int'>], but is type <class 'NoneType'>: None
    
    """
    if expected_type_clazz_or_tuple is None and value is None:
        return  # None == None
    # end if
    if isinstance(expected_type_clazz_or_tuple, tuple):
        expected_type_clazz_or_tuple = list(expected_type_clazz_or_tuple)
    if not isinstance(expected_type_clazz_or_tuple, list):
        expected_type_clazz_or_tuple = [expected_type_clazz_or_tuple]
    # end if
    expected_type_clazz_or_tuple.extend(more_clazzes)
    parameter_string = "the parameter {name} ".format(name=parameter_name) if parameter_name else ""
    for list_item in expected_type_clazz_or_tuple:
        if isinstance(list_item, (list, tuple)):
            expected_type_clazz_or_tuple.extend(list(list_item))
            continue
        if list_item is None:
            if value is None:
                assert value is None
                break  # is valid
            else:
                continue  # is None, but value is not.
                # end if
        if isinstance(list_item, type):
            if isinstance(value, list_item):
                assert isinstance(value, list_item)
                break  # is valid
                # end if
        else:
            if value is list_item or value == list_item:
                assert value is list_item or value == list_item
                break  # is valid
                # end if
                # end if
    else:  # for: -> is not valid, no break was used
        if len(expected_type_clazz_or_tuple) != 1:
            exception_text = (
                "{parameter_string}should be one of the types [{expected_type}], but is type {real_type}: {real_value!r}".format(
                    parameter_string=parameter_string, real_type=type(value), real_value=value,
                    expected_type=", ".join(repr(x) for x in expected_type_clazz_or_tuple)
                )
            )
        else:
            exception_text = (
                "{parameter_string}should be of type {expected_type!r}, but is type {real_type}: {real_value!r}".format(
                    parameter_string=parameter_string, expected_type=expected_type_clazz_or_tuple,
                    real_type=type(value), real_value=value
                )
            )
        # end if
        exception_text = exception_text[0].upper() + exception_text[1:]
        raise exception_clazz(exception_text)
        # end for
# end def assert_or_raise


def assert_or_raise(*args, **kwargs):
    warnings.warn("The `luckydonaldUtils.exceptions.assert_or_raise` method is deprecated, "
                  "use `assert_type_or_raise` instead", DeprecationWarning, 2)
    logger.warn("Deprecated: `luckydonaldUtils.exceptions.assert_or_raise` was renamed to `assert_type_or_raise`.")
    return assert_type_or_raise(*args, **kwargs)

# end def
