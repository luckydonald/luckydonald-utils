# -*- coding: utf-8 -*-
__author__ = 'luckydonald'
from .dependencies import import_or_install
from .files import gettempdir
from .Logging import logging  # pip install luckydonald-utils
logger = logging.getLogger(__name__)

import hashlib
import mimetypes
import os

DictObject = import_or_install("DictObject.DictObject", "DictObject")  # from DictObject import DictObject
magic = import_or_install("magic", "python-magic")  # import magic
requests = import_or_install("requests", "requests")  # import requests
from requests.packages.urllib3.exceptions import HTTPError

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X10.69; rv:4458.42) Gecko/4458 Firefox/69.0 Pon3Downloader'}


def get_json(url, objectify=True, **kwargs):
	kwargs.setdefault("headers", HEADERS)
	kwargs.setdefault("verify", False)
	json = requests.get(url, **kwargs).json()
	if objectify:
		return DictObject.objectify(json)
	return json


def download_file(url, used_cached=True, temp_dir=None, return_mime=False, return_buffer=False, progress_bar=False, **requests_kwargs):
	"""

	:param url:
	:param used_cached:
	:param temp_dir:
	:param return_mime:
	:param return_buffer: True: Don't write a file, just return the buffer. False: Write to file, return the files path
	:type  return_buffer: bool
	:return:
	"""
	requests_kwargs.setdefault("headers", HEADERS)
	requests_kwargs.setdefault("verify", False)
	if not return_buffer:
		if not temp_dir:
			temp_dir = gettempdir()
		file_name = url.split("/")[-1]
	#end if not return_buffer
	try:
		logger.debug("DL: Downloading from '{url}'.".format(url=url))
		image_buffer = requests.get(url, **requests_kwargs).content
	except HTTPError as e:
		logger.exception("DL: Error in URL '" + url + "'.\n" + str(e))
		raise
		#return (None, None) if return_mime else None
	except Exception as e:
		logger.exception("DL: Error in Download '" + url + "'.\n" + str(e))
		raise
		#return (None, None) if return_mime else None
	mime = magic.from_buffer(image_buffer, mime=True).decode("utf-8")
	suffix = (mimetypes.guess_extension(mime) if mime else ".unknown") or ".unknown"
	if return_buffer:
		logger.debug("DL: Requested Buffer, not creating/checking dirs/files.")
		if return_mime:
			return image_buffer, mime
		return image_buffer
	else: # -> not return_buffer:
		file_name = str(hashlib.md5(url.encode()).hexdigest()) + suffix
		file_name = os.path.join(temp_dir, file_name)
		if os.path.isfile(file_name):
			if used_cached:
				logger.debug("DL: File exists, using cached: %s" % file_name)
				if return_mime:
					return file_name, mime
				return file_name
			logger.debug("DL: File exists, redownloading: %s" % file_name)
		else:
			logger.debug("DL: File does not exist, downloading: %s" % file_name)
			if not os.path.exists(os.path.dirname(file_name)):
				logger.debug("DL: Download Folder does not exists. Creating.")
				os.makedirs(os.path.dirname(file_name))
		logger.debug("DL: Writing download from '%s' to file '%s'" % (url, file_name))
		try:
			with open(file_name, 'wb') as f:
				f.write(image_buffer)
		except Exception as e:
			logger.error("DL: Error in writing download to disk: '" + url + "' to '" + file_name + "'.\n" + str(e))
			file_name = None
		if return_mime:
			return file_name, mime
		return file_name
	#end if-else