# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

__version__ = "0.36"  # had a leading zero before version "0.20" (i.e. "0.019").  PyPI always removed that anyway.
VERSION = __version__

from sys import version as python_version

py2 = True if python_version < '3' else False
py3 = not py2