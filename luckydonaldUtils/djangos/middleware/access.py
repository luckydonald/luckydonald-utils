# -*- coding: utf-8 -*-
try:
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured, MiddlewareNotUsed
    from django.http import HttpResponseForbidden
except ImportError:  # pragma nocover
    from ...dependencies import import_or_install

    settings = import_or_install("django.conf.settings", "django")
    ImproperlyConfigured = import_or_install("django.ore.exceptions.ImproperlyConfigured", "django")
    MiddlewareNotUsed = import_or_install("django.ore.exceptions.MiddlewareNotUsed", "django")
    HttpResponseForbidden = import_or_install("django.http.HttpResponseForbidden", "django")
# end try
from ...logger import logging  # pip install luckydonald-utils
from ...dependencies import import_or_install

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)

IP = import_or_install("IPy.IP", "IPy")  # pip install IPy


class AllowFromIPMiddleware(object):
    """
    Allow only given IPs/CIDRs to access, else raise a `Http404` error. Is ignored when `DEBUG` is `True`.
    Checks ranges with https://pypi.python.org/pypi/IPy/.

    Set `ALLOW_FROM` to a list of IPs/CIDRs strings. To disable the Middleware, set it to `None`.

    Example:
    The *`settings.py`*
    ```
    ALLOW_FROM = ["8.8.8.8", "134.169.0.0/16"]
    ```

    To mimic the Apache syntax:
    > Allow from 134.169.
    One would write
    >>> ALLOW_FROM = ["134.169"]
    or
    >>> ALLOW_FROM = ["134.169.0.0/16"]
    in the `settings.py`.
    """
    buffered_ALLOW_FROM = []

    def __init__(self):
        try:
            allow_from = settings.ALLOW_FROM
        except AttributeError:
            raise ImproperlyConfigured('ALLOW_FROM setting does not exist.')
        if allow_from is None:
            raise MiddlewareNotUsed("ALLOW_FROM is None.")
        if not isinstance(allow_from, (list,tuple)):
            raise ImproperlyConfigured("ALLOW_FROM setting isn't a list of IP/CIDR strings.")
        if len(allow_from) == 0:
            raise ImproperlyConfigured("ALLOW_FROM is an empty list.")
        for ip in allow_from:
            self.buffered_ALLOW_FROM.append(IP(ip))
        #end for
    #end def __init__

    def process_request(self, request):
        remote_addr = request.META.get('HTTP_X_REAL_IP', request.META.get('REMOTE_ADDR', None))
        if any([remote_addr in ip for ip in self.buffered_ALLOW_FROM]):
            return  # allow
        if settings.DEBUG:
            logger.warn("The IP {remote_addr} should not be allowed, but is served anyway because DEBUG=True.".format(remote_addr=remote_addr))
            return  # allow
        return HttpResponseForbidden("Your ip {ip} is not allowed.".format(ip=remote_addr))   # forbid
            #end if DEBUG
        #end if
    #end def
#end class