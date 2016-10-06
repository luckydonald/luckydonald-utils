# -*- coding: utf-8 -*-
from sys import version as python_version

__author__ = 'luckydonald'
__version__ = "0.51"  # had a leading zero before version "0.20" (i.e. "0.019").  PyPI always removed that anyway.
VERSION = __version__

py2 = True if python_version < '3' else False
py3 = not py2

