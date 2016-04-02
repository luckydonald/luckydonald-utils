# -*- coding: utf-8 -*-
from .dependencies import import_or_install

import os
import sys
import errno
import logging
import tempfile
import mimetypes  # get mime types/suffix for DL.
import subprocess
magic = import_or_install("magic", "python-magic")  # pip install python-magic

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)


def gettempdir(temp_folder_name="luckydonald-utils"):
    temp_dir = tempfile.gettempdir()
    temp_dir = os.path.join(temp_dir, temp_folder_name)
    # py3
    # os.makedirs(temp_dir, exist_ok=True) #don't raise errors if existent.
    # py2/3 exist_ok workaround
    try:
        os.makedirs(temp_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    # end exist_ok workaround
    return temp_dir


# end def


def get_file_suffix(file_path=None, file_url=None):
    """
    This calls `get_file_mime()` to get the mime, and then calls `guess_extension()`.
    """
    mime = get_file_mime(file_path=file_path, file_url=file_url)
    return guess_extension(mime)


def guess_extension(mime):
    return mimetypes.guess_extension(type=mime or "")


def get_file_mime(file_path=None, file_url=None):
    if file_url:
        url = file_url
    elif file_path:
        from urllib.request import pathname2url
        url = pathname2url(file_path)
    else:
        raise AttributeError("Neither URL (file_url) nor local path (file_path) given.")
    mime = magic.from_file(file_path).decode("utf-8")
    return mime


def get_byte_mime(bytes):
    magic.from_buffer(bytes, mime=True).decode("utf-8")


def do_a_filename(input_file_name):
    output_file_name = input_file_name
    for replacer in [(":", ""), ("?", ""), ("*", ""), ("”", "\""), (">", ""), ("<", ""), ("|", "-"), ("\\", " "),
                     ("/", " ")]:
        output_file_name = output_file_name.replace(replacer[0], replacer[1])
    logger.debug("Filename '{old_filename}' is now '{new_filename}'.".format(old_filename=input_file_name,
                                                                             new_filename=output_file_name))
    return output_file_name


def mkdir_p(path):
    """
    like mkdir -p
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise



"""
def open_folder(folder_path)
"""  # for different Platforms
if sys.platform == 'darwin':  # Mac OS
    def open_folder(folder_path):
        subprocess.check_call(['open', '--', folder_path])


    def open_file_folder(file_path):
        subprocess.check_call(['open', '-R', '--', file_path])
elif sys.platform == 'linux2':  # linux, hopefully has gnome?
    def open_folder(folder_path):
        subprocess.check_call(['gnome-open', '--', folder_path])  # untested.


    def open_file_folder(file_path):
        open_folder(os.path.dirname(file_path))
elif sys.platform == 'win32':  # windows
    def open_folder(folder_path):
        subprocess.check_call(['explorer', folder_path])


    def open_file_folder(file_path):
        try:
            subprocess.check_call(['explorer', '/select,"%s"' % file_path])
        except:
            open_folder(os.path.dirname(file_path))
