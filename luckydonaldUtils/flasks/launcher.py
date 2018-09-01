# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging
import typing

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


class Launcher(object):
    """
    Allow ``flask``'s auto-reload to survive syntax errors and similar exceptions.
    Those will be displayed in the browser (if `debug` is on), or a generic message is provided.

    Also it will check if there is a debugger connected, and disable auto-reload.

    Finally it will detect if ``main.socketio`` exists, and launch that instead.
    (See https://flask-socketio.readthedocs.io/en/latest/#embedded-server for more info about that)

    ---

    Usage:

    Instead of

        >>> from somewhere.main import app
        >>>
        >>> if __name__ == "__main__":
        >>>     try:  # https://stackoverflow.com/a/338391/3423324
        >>>         import inspect
        >>>         debugger_connected = any(frame[1].endswith("pydevd.py") for frame in inspect.stack())
        >>>     except Exception:
        >>>         debugger_connected = False
        >>>     # end try
        >>>     auto_reload = not debugger_connected
        >>>     app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=auto_reload)
        >>> # end if

    you simply do

        >>> from luckydonaldUtils.flasks.launcher import Launcher
        >>>
        >>> with Launcher(__name__, host='0.0.0.0', port=8080, debug=True) as l:
        >>>     from somewhere import main
        >>>     l(main)
        >>> # end with
        >>>
        >>> app = l.app

    """

    def __init__(self, name, *args, **kwargs):
        """Run the SocketIO/Flask web server.
        :param name: The ``__name__`` variable.
        :param host: The hostname or IP address for the server to listen on.
                     Defaults to 127.0.0.1.
        :param port: The port number for the server to listen on. Defaults to
                     5000.
        :param debug: ``True`` to start the server in debug mode, ``False`` to
                      start in normal mode.
        :param use_reloader: ``True`` to forcefully enable the Flask reloader, ``False``
                             to forcefully disable it, ``None`` to disable automatically
                             if a debugger is connected. Defaults to ``None``.
        :param templates_use_reloader: ``None`` to enable the jijnja2 reloader only
                                       if no debugger is connected. ``True`` to
                                       forcefully enable it, and ``False`` to
                                       forcefully disable it. Defaults to ``None``.
        :param extra_files: A list of additional files that the Flask
                            reloader should watch. Defaults to ``None``.
        :param log_output: If ``True``, the server logs all incomming
                           connections. If ``False`` logging is disabled.
                           Defaults to ``True`` in debug mode, ``False``
                           in normal mode. Unused when the threading async
                           mode is used.
        :param kwargs: Additional web server options. The web server options
                       are specific to the server used in each of the supported
                       async modes. Note that options provided here will
                       not be seen when using an external web server such
                       as gunicorn, since this method is not called in that
                       case.
        """
        if name == '__main__':
            logging.add_colored_handler(level=logging.DEBUG)
        # end if
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.main = None
        self.did_fail = False
        self.exception = None

    # end def

    def __enter__(self):
        return self

    # end def

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            logger.exception('could not load app code:')
            self.main = None
            self.exception = (exc_type, exc_value, traceback)
        # end if
        return True  # suppress the exception  # https://docs.python.org/3/whatsnew/2.6.html#writing-context-managers

    # end def

    def __call__(self, main):
        self.main = main

    # end def

    @property
    def app(self):
        """
        :rtype:
        """
        if self.name == "__main__":
            # "__main__" means, this python file is called directly.
            # not to be confused with "main" (because main.py) when called from from nginx

            if self.main is None:
                # loading failed due to Syntax Errors or similar.
                self.did_fail = True
                self.fake_main_app()
            # end if

            debugger_connected = self.check_debugger()

            from flask.helpers import get_debug_flag
            do_debug = self.kwargs.pop('debug', get_debug_flag() or debugger_connected)
            self.kwargs.setdefault('use_debugger', debugger_connected)
            self.kwargs.setdefault('use_reloader', do_debug)
            self.kwargs.setdefault('templates_use_reloader', do_debug)

            N, T, F = None, True, False
            auto_reload, auto_reload_templates = {
                N: {
                    #  (flask, templates)
                    N: (not debugger_connected, not debugger_connected),
                    T: (not debugger_connected, T),  # flask, templates
                    F: (not debugger_connected, F),  # flask, templates
                },
                T: {
                    #  (flask, templates)
                    N: (T, T),  # flask, templates
                    T: (T, T),  # flask, templates
                    F: (T, F),  # flask, templates
                },
                F: {
                    #  (flask, templates)
                    N: (F, F),  # flask, templates
                    T: (F, F),  # flask, templates
                    F: (F, F),  # flask, templates
                },
            }[self.kwargs.pop('use_reloader')][self.kwargs.pop('templates_use_reloader')]

            logger.info('Debugger detected: {c}; Auto reload flask/templates {f}/{t}; Debug: {d}'.format(
                c=debugger_connected, f=auto_reload, t=auto_reload_templates, d=do_debug,
            ))

            # enable template auto reload
            if auto_reload_templates:
                self.main.app.jinja_env.auto_reload = True
                self.main.app.config['TEMPLATES_AUTO_RELOAD'] = True
            # end def

            self.kwargs.setdefault('host', '0.0.0.0')
            self.kwargs.setdefault('port', 8080)
            self.kwargs.setdefault('debug', do_debug)
            self.kwargs.setdefault('use_reloader', auto_reload)
            self.kwargs.setdefault('extra_files', [])

            if self.did_fail:
                from pathlib import Path
                import sys, os
                main_file = os.path.abspath(sys.modules['__main__'].__file__)
                print(main_file)
                self.kwargs['extra_files'].extend([x.absolute() for x in Path(main_file).rglob("*.py")])
                self.kwargs['debug'] = True
            # end if
            self.run_app()
        return self.main

    # end def

    def run_app(self):
        logger.debug("launching app with arguments: {!r}, {!r}".format(self.args, self.kwargs))
        if hasattr(self.main, 'socketio'):
            self.main.socketio.run(self.main.app, *self.args, **self.kwargs)
        else:
            self.main.app.run(*self.args, **self.kwargs)
        # end if

    # end def

    def fake_main_app(self, text='App not started', status=500):
        # loading failed due to Syntax Errors or similar.
        from flask import Flask
        self.main = lambda: 0  # fake main
        self.main.app = Flask(__name__)  # simple app
        self.main.app.debug = self.kwargs.get('debug', False)
        self.main.app.errorhandler(500)(self.error_handler(text, status))
        self.main.app.errorhandler(404)(self.error_handler(text, status))
    # end def

    def error_handler(self, text='App not started', status=500):
        from werkzeug.debug.tbtools import Traceback
        from werkzeug.debug import DebuggedApplication
        from flask import request

        def error_handler_inner_simple(e):
            return text, status

        # end def

        if not self.main.app.debug:
            return error_handler_inner_simple
        # end if

        d = DebuggedApplication(None)

        def error_handler_inner(e):
            if request.args.get('__debugger__') == 'yes' and request.args.get('cmd') == "resource":
                return d.get_resource(request, request.args.get('f'))
            # end if

            if self.exception:
                exc_type, exc_value, traceback = self.exception
                tb = Traceback(exc_type, exc_value, traceback)
                html = tb.render_full(evalex=False, secret=None, evalex_trusted=False)
                html = html.replace('</head>', '<style>.footer,.pastemessage{display:none}</style></head>')
                return html, status
            # end if
            return error_handler_inner_simple(e)

        # end def
        return error_handler_inner
    # end def

    @staticmethod
    def check_debugger():
        # check for debugger, as auto reloading with syntax errors always triggers the debugger,
        # which will jump to some random point where the code breaks, which is annoying.
        # If a debugger is connected, don't reload.

        # noinspection PyBroadException
        try:
            # https://stackoverflow.com/a/338391/3423324
            import inspect
            return any(frame[1].endswith("pydevd.py") for frame in inspect.stack())
        except Exception:
            return False
        # end try
    # end def
# end class
