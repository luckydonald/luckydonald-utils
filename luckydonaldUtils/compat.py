# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys

__author__ = 'luckydonald'
__all__ = ['py2', 'py3']

if sys.version < '3':  # python 2.7
    py2 = True
    py3 = False
else:
    py2 = False
    py3 = True  # This won't work with a future python 4, though.
# end if
