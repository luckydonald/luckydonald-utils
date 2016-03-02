# -*- coding: utf-8 -*-
from .. import py3
from ..logger import logging
from ..encoding import to_binary
from ..eastereggs.headers import get_headers

from cgi import parse_header, parse_multipart
from socket import error  # retry init'ing
from errno import EADDRINUSE  # retry init'ing
from time import sleep  # retry init'ing
from os import path

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)

try:
    if py3:
        # from socketserver import TCPServer
        from http.server import SimpleHTTPRequestHandler, HTTPServer
        from urllib.parse import parse_qs
    else:
        # from SocketServer import TCPServer
        from SimpleHTTPServer import SimpleHTTPRequestHandler
        from BaseHTTPServer import HTTPServer
        from urlparse import parse_qs
        # end if
except ImportError:
    raise  # try-except is only needed to satisfy PyCharm; to avoid PyCharm marking that as wrong import. As consequence the old error is reraised, as it really is an error.


# end try

class BetterHTTPRequestHandler(SimpleHTTPRequestHandler, object):
    def __init__(self, request, client_address, server):
        if py3:
            super(BetterHTTPRequestHandler, self).__init__(request, client_address, server)
        else:
            SimpleHTTPRequestHandler.__init__(self, request, client_address, server)
        self.static_files_dir = self.server.static_files_dir[:]  # force a copy

    def do_GET(self):
        logger.warn("do_GET is not overridden!")
        if self.path == "/":
            self.path = "/index.html"
        if False:  # Copy this and add your code here. ```if self.path == "/foo.bar":```
            pass
        else:
            self.path = self.static_files_dir + self.path  # e.g. localhost/123/foo.bar -> /path/to/script/webserver_files/123/foo.bar
            logger.debug("Requested file {file}".format(file=self.path))
            f = self.send_head()  # this handles 404'ing for us
            if f:
                try:
                    self.copyfile(f, self.wfile)
                finally:
                    f.close()
                    # end try
                    # end if
                    # end if-elif-else

    # end def

    def do_POST(self):
        logger.warn("do_POST is not overridden!")
        if self.path == "/":
            self.path = "/index.html"
        self.post_data = self.parse_POST()
        if False:  # Copy this and add your code here. ```if self.path == "/foo.bar":```
            pass
        else:
            self.path = self.static_files_dir + self.path  # e.g. localhost/123/foo.bar -> /path/to/script/webserver_files/123/foo.bar
            logger.debug("Requested file {file}".format(file=self.path))
            f = self.send_head()  # this handles 404'ing for us
            if f:
                try:
                    self.copyfile(f, self.wfile)
                finally:
                    f.close()
                # end try
            # end if
        # end if-elif-else
    # end def

    def parse_POST(self):
        ctype, pdict = parse_header(self.headers['content-type'])
        if "boundary" in pdict:
            pdict["boundary"] = to_binary(pdict["boundary"])
        if ctype == 'multipart/form-data':
            postvars = parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers['content-length'])
            postvars = parse_qs(
                self.rfile.read(length),
                keep_blank_values=1)
        else:
            postvars = {}
        return postvars

    # end def

    def write_text(self, msg, content_type="text/plain", is_binary=False):
        """
        Makes answering with text/data easier.

        :param msg: The text to send to the browser/client.
        :keyword content_type: If you don't like it to be text, change that here.
        :keyword is_binary: Text (unicode) needs to be converted to binary. If you already have binary (e.g. an PNG as binary data) you can set that here.
        :return: Nothing.
        """
        # Now do servery stuff.
        if not is_binary:
            msg = to_binary(msg)
        if msg is None:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", str(len(msg)))
        for k, v in get_headers().items():
            self.send_header(k, v)
        self.send_header("X-Backend-created-by", "luckydonald")
        self.send_header("X-Licence", "Luna-Will-Cry-If-You-Modify-Or-Redistribute 1.0 or later")
        self.send_header("X-Licence-URL", "flutterb.at/lwc-1-0")
        self.end_headers()
        self.wfile.write(msg)
        return
    # end def

    def translate_path(self, path_):
        """
         Now accepts local fitting paths automatically
        E.g. "/path/to/www-dir/foo.png" is valid if that folder exists.
        Now it won't change the path to "/path/to/www-dir/foo.png/path/to/www-dir/foo.png", like it did before.
        :param path: path for the webserver.
        :return:
        """
        if path.exists(path_):
            return path_
        if py3:
            super(BetterHTTPRequestHandler, self).translate_path(path_)
        else:
            SimpleHTTPRequestHandler.translate_path(self, path_)
        return path_
    # end def

    def log_message(self, format, *args):
        logger.info(
            "%s - %s - [%s] %s\n" % (self.client_address[0], self.path, self.log_date_time_string(), format % args))

    def log_request(self, code='-', size='-'):
        logger.debug('%s - %s - "%s" %s %s', self.client_address[0], self.path, self.requestline, str(code), str(size))

    def log_error(self, format, *args):
        logger.error("%s - %s - %s" % (self.client_address[0], self.path, format % args))
    # end def
# end class


def start_a_webserver(handler, port, host="", static_files_dir=None):
    """
    Starts a ```TCPServer```, using the given ```handler```,
    :param handler: An handler instance, e.g. an ```BetterHTTPRequestHandler```
    :param port: The port where to serve on. For example ```80``` or ```8080``` for HTTP (```80``` often needs root privileges)
    :keyword host: Optional. A host where to serve on. If an empty string ```""``` (default) is given, all incoming connections are allowed. (from localhost, from lan, from internet, etc.)
    :keyword static_files_dir: Optional. Set the ```static_files_dir``` of an ```BetterHTTPRequestHandler``` handler.
    :return: The ```TCPServer``` created.
    """
    # assert (isinstance(handler, BetterHTTPRequestHandler))  # BaseRequestHandler?
    # handler = BetterHTTPRequestHandler()
    httpd = None
    started = False
    while not started:
        try:
            httpd = HTTPServer((host, port), handler)
            if issubclass(handler, BetterHTTPRequestHandler):
                if not static_files_dir:
                    logger.warn(
                        "`static_files_dir` kwarg-parameter should be used when a `BetterHTTPRequestHandler` is used.")
                httpd.static_files_dir = static_files_dir
            started = True
        except error as e:
            if e.errno in [EADDRINUSE]:
                logger.warn("Starting Server failed. Address already in use. Retrying.")
                sleep(1)
            else:
                raise
            # end if-else
        # end try
    # end while
    return httpd
# end def
