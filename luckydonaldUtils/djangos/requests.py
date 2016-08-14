# -*- coding: utf-8 -*-
"""
Tools to use with django's HttpRequests.
"""
try:
    from django.middleware.csrf import CsrfViewMiddleware
except ImportError:  # pragma nocover
    from ..dependencies import import_or_install

    CsrfViewMiddleware = import_or_install("django.middleware.csrf.CsrfViewMiddleware", "django")
# end try


__author__ = 'luckydonald'


def check_csrf(request):
    """
    This checks if the csrf check was passed.

    :param request: the request
    :type  request: django.http.HttpRequest

    :return: If it did pass the check.
    :rtype : bool
    """
    reason = CsrfViewMiddleware().process_view(request, None, (), {})
    if reason:
        # CSRF failed
        return False
    return True


# end def

def GET_to_bool(request, key):
    """
    Parses a GET parameter in the request as bool.
    "true" becomes True, "false" becomes False, "null" becomes None.

    :param request: the request
    :type  request: django.http.HttpRequest

    :param key: the key in request.GET
    :type  key: str

    :return: Boolean or None
    :rtype : bool | None
    """
    clone_manual = request.GET[key]
    assert clone_manual in ["true", "false", "null"]
    clone_manual_bool = None
    if clone_manual == "true":
        clone_manual_bool = True
    if clone_manual == "false":
        clone_manual_bool = False
    return clone_manual_bool
