# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

VERSION = "0.20"  # had a leading zero before version "0.20" (i.e. "0.019").  PyPI always removed that.


from sys import version as python_version

py2 = True if python_version < '3' else False
py3 = not py2