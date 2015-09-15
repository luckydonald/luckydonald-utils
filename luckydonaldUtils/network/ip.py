# -*- coding: utf-8 -*-

__author__ = 'luckydonald'

from .. import py3

if py3:
	def binary_ip_to_str(host):
		return ".".join([str(x) for x in host])
else:
	def binary_ip_to_str(host):
		return ".".join([str(ord(x)) for x in host])