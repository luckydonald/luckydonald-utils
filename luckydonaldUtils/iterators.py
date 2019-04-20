# -*- coding: utf-8 -*-
from .logger import logging
from .functions import deprecated

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)

@deprecated(message="Instead of `for obj, i in iter_with_i(iterator=iterable, i_start=start)` use `for i, obj in enumerate(iterable, start=start)`.")
def iter_with_i(iterator, i_start=0):
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
    # end for
# end def


def chunks_known_length(iterable, size, length=None):
    """
    Yield successive `size`-sized chunks from `iterable`,
    if the length of `iterable is already known or easy to compute.

    https://stackoverflow.com/a/312464/3423324

    :param iterable: The object you want to split into pieces.

    :param size: The size each of the resulting pieces should have.
    :type  size: int

    :param length: Optional. Length of the `iterable`.
                   If set to `None` (default), the length get calculated automatically.
    :type  length: None | int
    """
    if length is None:
        len(iterable)
    # end if
    for i in range(0, length, size):
        yield iterable[i:i + size]
    # end for
# end for


def chunks(iterable, size):
    """
    Yield successive chunks from `iterable`, being `size` long.

    https://stackoverflow.com/a/55776536/3423324

    :param iterable: The object you want to split into pieces.
    :param size: The size each of the resulting pieces should have.
    """
    i = 0
    while True:
        sliced = iterable[i:i + size]
        if len(sliced) == 0:
            # to suppress stuff like `range(max, max)`.
            break
        # end if
        yield sliced
        if len(sliced) < size:
            # our slice is not the full length, so we must have passed the end of the iterator
            break
        # end if
        i += size  # so we start the next chunk at the right place.
    # end while
# end def
