# -*- coding: utf-8 -*-

from __future__ import division

__author__ = 'luckydonald'

from .dependencies import import_or_install
from .files import gettempdir
from .encoding import to_binary as b
import hashlib
import mimetypes
import sys
import os

from DictObject import DictObject

try:
    import magic
except ImportError:  # pragma nocover
    magic = import_or_install("magic", "python-magic")  # import magic
# end try

try:
    import requests
    from requests.packages.urllib3.exceptions import HTTPError
except ImportError:  # pragma nocover
    requests = import_or_install("requests", "requests")  # import requests
    HTTPError = import_or_install("requests.packages.urllib3.exceptions.HTTPError", "requests")
# end try

try:
    import progressbar
    from progressbar import Widget
    from progressbar import ETA, Percentage, Bar, FileTransferSpeed, ProgressBar
except ImportError:  # pragma nocover
    progressbar_version = ("progressbar" if sys.version < "3.3" else "progressbar33")
    import_or_install("progressbar", progressbar_version)
    Widget = import_or_install("progressbar.Widget import Widget", progressbar_version)
    ETA = import_or_install("progressbar import ETA", progressbar_version)
    Percentage = import_or_install("progressbar import Percentage", progressbar_version)
    Bar = import_or_install("progressbar import Bar", progressbar_version)
    FileTransferSpeed = import_or_install("progressbar import FileTransferSpeed", progressbar_version)
    ProgressBar = import_or_install("progressbar import ProgressBar", progressbar_version)
# end try

import logging

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X10.69; rv:4458.42) Gecko/4458 Firefox/69.0 Pon3Downloader'}


def get_json(url, objectify=True, **kwargs):
    kwargs.setdefault("headers", HEADERS)
    json = requests.get(url, **kwargs).json()
    if objectify:
        return DictObject.objectify(json)
    return json


def download_file(url, used_cached=True, download_folder=None, temp_folder_name="luckydonald-utils", return_mime=False,
                  return_buffer=False, progress_bar=False, **requests_kwargs):
    """
    Downloads a file. Filename is the md5 hash of the url.

    :param url: The url you want to download.

    :param used_cached: If the url was already downloaded, that file will not be overwritten.
    The files name is just a hash of the url. So the same filename means same hash means same url.

    :param download_folder:
    Path to the download dir.
    If None, a folder will be created inside the /tmp/ folder equivalent of your system, with the name from `temp_folder_name`.

    :param temp_folder_name:
    Name of the folder to be created/used in the /tmp/ equivalent of your system.
    This is option ignored, if `download_folder` is given. 	Default: "luckydonald-utils"

    :param return_mime: If set to true, a (filename, mime) tuple is returned, else just the filename.

    :param return_buffer: If set to true, nothing will be written to disk,
    you'll get the buffer returned instead of the filename.

    :param progress_bar: If it should display a progress bar.

    :param **requests_kwargs: All other arguments are piped to the requests.get() call.

    :return: The path of the file. If `return_buffer` is true, instead it contains the buffer.
    If `return_mime` is true, it is a tuple of that and the mime, (file_path, mime) or (buffer, mime)

    """
    requests_kwargs.setdefault("headers", HEADERS)
    bar = Bar(marker="#", left="[", right="]")
    if not return_buffer:
        if not download_folder:
            download_folder = gettempdir(temp_folder_name=temp_folder_name)
        # end if not return_buffer
    try:
        logger.debug("DL: Downloading from '{url}'.".format(url=url))
        if progress_bar:
            requests_kwargs["stream"] = True
            response = requests.get(url, **requests_kwargs)
            total_length = response.headers.get('content-length')
            if total_length is None:  # no content length header
                widgets = ["Downloading Song: ", bar, " ",
                           DoneWidget(init="Connecting...", started="Unknown Size.", finished="Complete.")]
                pbar = ProgressBar(widgets=widgets).start()
                logger.debug("No content-length provided.")
                image_buffer = response.content
                pbar.finish()
            else:
                dl = 0
                image_buffer = b("")
                total_length = int(total_length)
                widgets = ["Downloading Song: ", bar, " ", Percentage(), " ", FileTransferSpeed(), ", ", ETA()]
                pbar = ProgressBar(widgets=widgets, maxval=total_length).start()
                for data in response.iter_content(chunk_size=int(total_length / 100)):
                    dl += len(data)
                    image_buffer += data
                    pbar.update(dl)
                # end for
                pbar.finish()
                # now is downloaded.
                logger.debug("Download completed.")
        else:
            image_buffer = requests.get(url, **requests_kwargs).content
    except HTTPError as e:
        logger.exception("DL: Error in URL '" + url + "'.\n" + str(e))
        raise
        # return (None, None) if return_mime else None
    except Exception as e:
        logger.exception("DL: Error in Download '" + url + "'.\n" + str(e))
        raise
        # return (None, None) if return_mime else None
    mime = magic.from_buffer(image_buffer, mime=True).decode("utf-8")
    suffix = (mimetypes.guess_extension(mime) if mime else ".unknown") or ".unknown"
    suffix = '.jpg' if suffix == '.jpe' else suffix  # nobody uses that.
    if return_buffer:
        logger.debug("DL: Requested Buffer, not creating/checking dirs/files.")
        if return_mime:
            return image_buffer, mime
        return image_buffer
    else:  # -> not return_buffer:
        file_name = str(hashlib.md5(url.encode()).hexdigest()) + suffix
        file_name = os.path.join(download_folder, file_name)
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
        # end if-else


class DoneWidget(Widget):
    """
    Can display 3 values.
    """

    def __init__(self, init="Not started.", started="Running.", finished="Done."):
        self.init_text = init
        self.started_text = started
        self.finished_text = finished

    def update(self, pbar):
        if pbar.start_time is None:
            return self.init_text
        elif not pbar.finished:
            return self.started_text
        else:
            return self.finished_text
