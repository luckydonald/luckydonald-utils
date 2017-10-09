# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys

__author__ = 'luckydonald'

if sys.version < '3':  # python 2.7
    text_type = unicode
    binary_type = str
    native_type = binary_type
    unicode_type = text_type  # because I can't remember to use text_type
    long_int = long

    def to_native(x):
        return to_binary(x)
        # end def
else:  # python 3
    text_type = str
    binary_type = bytes
    native_type = text_type
    unicode_type = text_type
    long_int = int

    def to_native(x):
        return to_unicode(x)
        # end def
# end if


def to_binary(x):
    if isinstance(x, text_type):
        return x.encode("utf-8")
    elif isinstance(x, binary_type):
        return x
    else:
        return to_binary(str(x))  # str() can fail.  # do i need bytes() here with py3 (because ascii and stuff?) ?
        # end if


# end def


def to_unicode(x):
    if isinstance(x, binary_type):
        return x.decode("utf-8")
    elif isinstance(x, text_type):
        return x
    else:
        return to_unicode(str(x))  # str() can fail.
        # end if

# end def
