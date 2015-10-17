# -*- coding: utf-8 -*-
__author__ = 'luckydonald'
from django.middleware.csrf import CsrfViewMiddleware

def check_csrf(request):
	reason = CsrfViewMiddleware().process_view(request, None, (), {})
	if reason:
		# CSRF failed
		return False
	return True
