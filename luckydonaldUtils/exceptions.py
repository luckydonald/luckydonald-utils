# -*- coding: utf-8 -*-

import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)


def assert_or_raise(value, expected_type_clazz_or_tuple, *more_clazzes, exception_clazz=TypeError):
    """
    A better `assert(isinstance(a, B)` because it supports `None` (as well as some other types except tuple or list), and an nice exception text.

    :param value: The variable to check
    :param expected_type_clazz_or_tuple: a class or value  or  list/tuple of that
    :param *more_clazzes: even more classes or values
    :param exception_clazz: type of the exception raised. Defaults to :class:`TypeError`

    :raises: exception_clazz
    :return: Nothing


    Examples/Tests:

    Check if None:

        >>> val = None
        >>> assert_or_raise(val, None)

        >>> assert_or_raise(val, [None])

    Check multible:

        >>> assert_or_raise(val, [None, bool, int])

        >>> assert_or_raise(val, (None, bool, int))

        >>> assert_or_raise(val, None, bool, int)

        >>> assert_or_raise(val, [None, bool], int)

        >>> assert_or_raise(val, None, [bool, int])

        >>> assert_or_raise(1, [None, bool, int])

        >>> assert_or_raise(True, [None, bool, int])

        >>> assert_or_raise(1, [None, bool, 1])

        >>> assert_or_raise(True, [None, True, int])

    Failing asserts:

        >>> assert_or_raise("True", [None, True, int])  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        TypeError: Should be one of the types [None, True, <class 'int'>], but is type <class 'str'>: True

        >>> assert_or_raise(None, [True, int])  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        TypeError: Should be one of the types [True, <class 'int'>], but is type None: None


    Custom Exception Type:

        >>> assert_or_raise(None, [True, int], exception_clazz=ValueError)  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        ValueError: Should be one of the types [True, <class 'int'>], but is type None: None

    """
    if expected_type_clazz_or_tuple is None and value is None:
        return  # None == None
    if isinstance(expected_type_clazz_or_tuple, tuple):
        expected_type_clazz_or_tuple = list(expected_type_clazz_or_tuple)
    if not isinstance(expected_type_clazz_or_tuple, list):
        expected_type_clazz_or_tuple = [expected_type_clazz_or_tuple]
    # end if
    expected_type_clazz_or_tuple.append(more_clazzes)
    for list_item in expected_type_clazz_or_tuple:
        if isinstance(list_item, (list, tuple)):
            expected_type_clazz_or_tuple.extend(list(list_item))
            continue
        if list_item is None:
            if value is None:
                break  # is valid
            else:
                continue  # is None, but value is not.
                # end if
        if isinstance(list_item, type):
            if isinstance(value, list_item):
                break  # is valid
                # end if
        else:
            if value is list_item or value == list_item:
                break  # is valid
                # end if
                # end if
    else:  # for: is not valid, no break was used
        if len(expected_type_clazz_or_tuple) != 1:
            raise exception_clazz(
                "Should be one of the types [{expected_type}], but is type {real_type}: {real_value}"
                    .format(
                    expected_type=", ".join(str(x) for x in expected_type_clazz_or_tuple), real_type=type(value),
                    real_value=value
                )
            )
        else:
            raise exception_clazz(
                "Should be of type {expected_type}, but is type {real_type}: {real_value}".format(
                    expected_type=expected_type_clazz_or_tuple, real_type=type(value), real_value=value
                ))
            # end if
            # end for

# end def assert_or_raise
