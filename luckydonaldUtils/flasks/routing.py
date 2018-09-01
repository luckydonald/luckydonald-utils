# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging

try:
    from werkzeug.exceptions import HTTPException
    from werkzeug.routing import MapAdapter
    from flask.globals import _app_ctx_stack, _request_ctx_stack
    from flask import url_for, request

except ImportError:  # pragma nocover
    from ..dependencies import import_or_install

    MapAdapter = import_or_install("werkzeug.routing.MapAdapter", "werkzeug")
    HTTPException = import_or_install("werkzeug.exceptions.HTTPException", "werkzeug")
    _app_ctx_stack = import_or_install("flask.globals._app_ctx_stack", "flask")
    url_for, request = import_or_install("flask.url_for", "flask"), import_or_install("flask.request", "flask")
    _request_ctx_stack = import_or_install("flask.globals._request_ctx_stack", "flask")
# end try


__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


def route_for(url, is_full_url=False):
    """
    Basically `flask.url_for` in reverse.
    You give a url, it gives you the route and the required arguments.

    Example:
    >>> @app.route('/foobar/<argument>')
    ... def some_test(argument):
    ...     pass
    ... # end def

    >>> route_for("https://example.com/foobar/lel", is_full_url=True)



    :param url: The url you want the route for.
    :param is_full_url: If true it will try to remove `{adapter.url_scheme}://{adapter.server_name}` from the beginning,
                        and return `None` if it fails.
    :return: you get a tuple in the form ``(endpoint, arguments)`` if there is a match, else if anything goes wrong, ``None``.
    :rtype: None | tuple of (str, list of str)
    """
    adapter = _app_ctx_stack.top.url_adapter if _app_ctx_stack and _app_ctx_stack.top and _app_ctx_stack.top.url_adapter else _request_ctx_stack.top.url_adapter
    assert isinstance(adapter, MapAdapter)
    if is_full_url:
        if not url.startswith(adapter.url_scheme + '://'):
            logger.debug("Url doesn't start with '{}://'.".format(adapter.url_scheme))
            return None
        url = url[len(adapter.url_scheme) + 3:]
        # end if
        if not url.startswith(adapter.server_name):
            logger.debug("Url doesn't start with '{}://{}'.".format(adapter.url_scheme, adapter.server_name))
            return None
        # end if
        url = url[len(adapter.server_name):]
        if "?" in url:
            url = url.split("?", 1)[0]
            logger.debug("Removed query segment.")
        # end if
        if "#" in url:
            url = url.split("#", 1)[0]
            logger.debug("Removed hash segment.")
        # end if
    # end if

    try:
        return adapter.match(url, method=request.method, return_rule=False)
    except HTTPException as e:
        logger.debug("Route not found: {}".format(e))
        return None
    # end try


# end def


def get_safe_next(url=None, full_url_only=True, allow_self=False, old_referrer_must_match=False,
                  generate_url=True):
    """
    Checks if the specified ``url`` in like a ``?next=`` parameter is part of our registered routes,
    and thus seems safe to redirect to.

    Additionally you can choose:

    - if you want to require the value to be a full url, with protocol, domain, etc. (``full_url_only``),
    - if you want to allow redirect to the same page again which might cause a redirect loop (``allow_self``),
    - if you need the http referrer the browser sent to match the next ``url``,
      i.e. it goes back to the previous url (``old_referrer_must_match``)

    :param url: The value for the next url. Defaults to ``request.args.get('next')``.
    :param full_url_only: If the next url should be a full url, with ``http://www.domain.com/`` and whatnot.
    :param allow_self: If redirect to self is valid. Default: ``False``.

    :param old_referrer_must_match: Default: ``False``. Don't check referrer.
                                    ``True`` to require it to resolve to the same endpoint as ``next`` does.
                                    A ``str`` to require it to match that endpoint.

    :type  old_referrer_must_match: bool|str

    :param generate_url: If we should return an url string (``True``), or just the (``route``, ``params``) tuple (``False``).
    :type  generate_url: bool

    :return: If anything goes wrong, or you get no match, ``None`` is returned. Else, if ``generate_url`` is ``True``, you get an url string you can redirect to, or if ``generate_url`` is ``False`` you get a tuple in the form ``(endpoint, arguments)``.
    :rtype: None | str | tuple of (str, dict)
    """
    if not url:
        url = request.args.get('next', None)
    # end if
    if not url:
        logger.debug('No next parameter.')
        return None
    # end if
    param_route = route_for(url, is_full_url=full_url_only)
    if not param_route:
        logger.debug('No route found for next parameter.')
        return None
    # end if
    if old_referrer_must_match:
        # needed_referrer_endpoint  is either the string endpoint in old_referrer_must_match,
        # or the route calculated for the `next` param, param_route[0]
        if not request.referrer:
            logger.debug('No referrer data.')
            return None
        # end if

        needed_referrer_endpoint = old_referrer_must_match if isinstance(old_referrer_must_match, str) else param_route[
            0]
        referrer_route = route_for(request.referrer, is_full_url=True)

        if referrer_route[0] != needed_referrer_endpoint:
            logger.debug('Referrer endpoint {!r} does not fit needed endpoint {!r}.'.format(
                referrer_route[0], needed_referrer_endpoint
            ))
            return None
        # end if
    # end if
    if not allow_self and param_route[0] == request.endpoint:
        # don't redirect to self
        logger.debug('Redirect to self is not allowed.')
        return None
    # end if
    logger.debug('Next url ok: {!r}'.format(param_route[0]))
    if generate_url:
        return url_for(param_route[0], **param_route[1])
    # end if
    return param_route
# end def
