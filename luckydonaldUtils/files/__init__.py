# -*- coding: utf-8 -*-
from ..functions import deprecated
from ..logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)

__all__ = [
    "basics", "mime", "name", "temp", "tree",
    # for downwards compatibility:
    'mkdir_p', 'open_file_folder', 'open_folder', 'get_byte_mime', 'get_file_mime', 'guess_extension',
    'get_file_suffix', 'do_a_filename', 'gettempdir'
]
__IMPORT_CHANGED_MESSAGE = (
    "Import path changed. Please import {func_name} from luckydonaldUtils.files.{where} instead. "
    "This import will be removed in the future."
)


@deprecated(__IMPORT_CHANGED_MESSAGE.format(func_name="mkdir_p", where="basics"))
def mkdir_p(path):
    from .basics import mkdir_p
    return mkdir_p(path)


# end def


@deprecated(__IMPORT_CHANGED_MESSAGE.format(func_name="open_file_folder", where="basics"))
def open_file_folder(file_path):
    from .basics import open_file_folder
    return open_file_folder(file_path)


# end def


@deprecated(__IMPORT_CHANGED_MESSAGE.format(func_name="open_folder", where="basics"))
def open_folder(folder_path):
    from .basics import open_folder
    return open_folder(folder_path)


# end def


@deprecated(__IMPORT_CHANGED_MESSAGE.format(func_name="get_byte_mime", where="mime"))
def get_byte_mime(bytes):
    from .mime import get_byte_mime
    return get_byte_mime(bytes)


# end def


@deprecated(__IMPORT_CHANGED_MESSAGE.format(func_name="get_file_mime", where="mime"))
def get_file_mime(file_path=None, file_url=None):
    from .mime import get_file_mime
    return get_file_mime(file_path=file_path, file_url=file_url)


# end def


@deprecated(__IMPORT_CHANGED_MESSAGE.format(func_name="guess_extension", where="mime"))
def guess_extension(mime):
    from .mime import guess_extension
    return guess_extension(mime)


# end def


@deprecated(__IMPORT_CHANGED_MESSAGE.format(func_name="get_file_suffix", where="mime"))
def get_file_suffix(file_path=None, file_url=None):
    from .mime import get_file_suffix
    return get_file_suffix(file_path=file_path, file_url=file_url)


# end def


@deprecated(__IMPORT_CHANGED_MESSAGE.format(func_name="do_a_filename", where="name"))
def do_a_filename(input_file_name):
    from .name import do_a_filename
    return do_a_filename(input_file_name)


# end def


@deprecated(__IMPORT_CHANGED_MESSAGE.format(func_name="gettempdir", where="temp"))
def gettempdir(temp_folder_name="luckydonald-utils"):
    from .temp import gettempdir
    return gettempdir(temp_folder_name=temp_folder_name)

# end def
