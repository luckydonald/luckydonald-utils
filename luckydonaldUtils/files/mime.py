from ..dependencies import import_or_install

try:
    import magic
except ImportError:  # pragma nocover
    magic = import_or_install("magic", "python-magic")  # pip install python-magic
# end try
import mimetypes


def guess_extension(mime):
    """Shortcut for getting extension to a given mime string.
    The parameter mime can be None"""
    return mimetypes.guess_extension(type=mime or "")


def get_file_mime(file_path=None, file_url=None):
    """
    Shortcut to get the mime from either

    :param file_path:
    :param file_url:
    :return:
    """
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
    """
    Shortcut to get a mime from bytes in a variable.

    :param bytes:
    :return:
    """
    magic.from_buffer(bytes, mime=True).decode("utf-8")


def get_file_suffix(file_path=None, file_url=None):
    """
    This calls `get_file_mime()` to get the mime, and then calls `guess_extension()`.
    """
    mime = get_file_mime(file_path=file_path, file_url=file_url)
    return guess_extension(mime)
