# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

from .. import py3
from ..logger import logging
from luckydonaldUtils.encoding import to_binary

logger = logging.getLogger(__name__)

if py3:
	try:
		from socketserver import TCPServer
		from http.server import SimpleHTTPRequestHandler
	except ImportError:
		raise  # Try is only needed to satisfy PyCharm, to not to mark that as wrong.
else:
	from SocketServer import TCPServer
	from SimpleHTTPServer import SimpleHTTPRequestHandler
from socket import error  # retry init'ing
from errno import EADDRINUSE  # retry init'ing
from time import sleep  # retry init'ing
import os


class BetterHTTPRequestHandler(SimpleHTTPRequestHandler, object):
	def __init__(self, request, client_address, server, www_dir):
		if py3:
			super(BetterHTTPRequestHandler, self).__init__(request, client_address, server)
		else:
			SimpleHTTPRequestHandler.__init__(self, request, client_address, server)
		self.folder = www_dir

	def do_GET(self):
		logger.warn("do_GET is not overridden!")
		if self.path == "/":
			self.path = "/index.html"
		if False:  # You could add your code here. ```if self.path == "/foo.bar":```
			pass
		else:
			self.path = self.folder + self.path  # e.g. localhost/123/foo.bar -> /path/to/script/webserver_files/123/foo.bar
			logger.debug("Requested file {file}".format(file=self.path))
			f = self.send_head()  # this handles 404'ing for us
			if f:
				try:
					self.copyfile(f, self.wfile)
				finally:
					f.close()
				# end try
				# end if
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
		self.end_headers()
		self.wfile.write(msg)
		return
	# end def

	def translate_path(self, path):
		"""
		 Now accepts local fitting paths automatically
		E.g. "/path/to/www-dir/foo.png" is valid if that folder exists.
		Now it won't change the path to "/path/to/www-dir/foo.png/path/to/www-dir/foo.png", like it did before.
		:param path: path for the webserver.
		:return:
		"""
		if os.path.exists(path):
			return path
		if py3:
			super(BetterHTTPRequestHandler, self).translate_path(path)
		else:
			SimpleHTTPRequestHandler.translate_path(self, path)
		return path
	# end def

	def log_message(self, format, *args):
		logger.info("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format % args))

	def log_request(self, code='-', size='-'):
		logger.debug('%s - - "%s" %s %s', self.client_address[0], self.requestline, str(code), str(size))

	def log_error(self, format, *args):
		logger.error("%s - - %s" % (self.client_address[0], format % args))
#end class


def start_a_webserver(handler, port, host=""):
	"""
	Starts a ```TCPServer```, using the given ```handler```,
	:param handler: An handler instance, e.g. an ```BetterHTTPRequestHandler```
	:param port: The port where to serve on. For example ```80``` or ```8080``` for HTTP (```80``` often needs root privileges)
	:keyword host: Optional. A host where to serve on. If an empty string ```""``` (default) is given, all incoming connections are allowed. (from localhost, from lan, from internet, etc.)
	:return: The ```TCPServer``` created.
	"""
	#assert (isinstance(handler, BetterHTTPRequestHandler))  # BaseRequestHandler?
	#handler = BetterHTTPRequestHandler()
	httpd = None
	started = False
	while not started:
		try:
			httpd = TCPServer((host, port), handler)
			started = True
		except error as e:
			if e.errno in [EADDRINUSE]:
				logger.warn("Starting Server failed. Address already in use. Retrying.")
				sleep(1)
			else:
				raise
			#end if-else
		#end try
	#end while
	return httpd
#end def
