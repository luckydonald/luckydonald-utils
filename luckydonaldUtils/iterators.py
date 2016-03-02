# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

from luckydonaldUtils.logger import logging  # pip install luckydonald-utils
logger = logging.getLogger(__name__)


def iter_with_i(iterator, i_start = 0):
    """
    Yields a tuple of the iterator result and an i(iterator_result, i),
    i incrementing each time.

    Example:
        >>> some_list = ["a","b"]

        >>> for iterator_result, i in iter_with_i(some_list)
        ... 	print("iterator is {}, i is {}".format(iterator_result, i))
        iterator is a, i is 0
        iterator is b, i is 1

    :param iterator: Your iterable object (lists etc.)
    :keyword i_start: Where to start counting. Default is `0`
    """
    i = i_start
    for iterator_result in iterator:
        yield (iterator_result, i)
        i += 1

