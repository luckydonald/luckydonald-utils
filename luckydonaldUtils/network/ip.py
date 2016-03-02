# -*- coding: utf-8 -*-
from .. import py3

__author__ = 'luckydonald'


if py3:
    def binary_ip_to_str(host):
        return ".".join([str(x) for x in host])
else:
    def binary_ip_to_str(host):
        return ".".join([str(ord(x)) for x in host])