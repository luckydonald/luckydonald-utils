# -*- coding: utf-8 -*-
import subprocess
import sys

__author__ = 'luckydonald'


def pip_install(*args):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *args])
