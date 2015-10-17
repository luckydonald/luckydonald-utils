# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

from ..dependencies import import_or_install
import_or_install("django", "django")

from django.middleware.csrf import CsrfViewMiddleware

def check_csrf(request):
	reason = CsrfViewMiddleware().process_view(request, None, (), {})
	if reason:
		# CSRF failed
		return False
	return True
