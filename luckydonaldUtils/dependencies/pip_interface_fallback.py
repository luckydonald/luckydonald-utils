# -*- coding: utf-8 -*-

import pip
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


def pip_install(*args):
    return pip.main(["install"].append(args))
