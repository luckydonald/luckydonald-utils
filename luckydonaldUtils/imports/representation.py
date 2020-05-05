#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


def split_path(path):
    """
    Splits the text and build a nice import statement from it.
    Note: only well defined import paths are supported. Not something invalid like '..foo.bar..'.


    >>> split_path('foo.bar.Batz')
    ('foo.bar', 'Batz')

    >>> split_path('..lel')
    ('..', 'lel')

    >>> split_path('.lul')
    ('.', 'lul')

    >>> split_path('lol')
    ('', 'lol')

    >>> split_path('...na.na.na.na.na.na.Batman')
    ('...na.na.na.na.na.na', 'Batman')

    >>> split_path('...........yolo.swagger')
    ('...........yolo', 'swagger')

    :param path: The path to split.
    :type  path: str

    :return: The import text, like `from x import y` or `import z`
    :rtype: tuple(str)|Tuple[str, str]
    """
    last_dot_position = path.rfind('.')
    if last_dot_position == -1:
        # no dot found.
        import_path = ''
        import_name = path
    else:
        import_path = path[:last_dot_position + 1]
        import_name = path[last_dot_position + 1:]

        # handle 'foo.bar.Baz' not resulting in 'foo.bar.', i.e. remove the dot at the end.
        if import_path.rstrip('.') != '':
            # e.g. not '....'
            import_path = import_path.rstrip('.')
    # end if

    return import_path, import_name
# end def


def path_to_import_text(path):
    """
    Splits the text and build a nice import statement from it.
    Note: only well defined import paths are supported. Not something invalid like '..foo.bar.'

    >>> path_to_import_text('foo.bar.Batz')
    'from foo.bar import Batz'

    >>> path_to_import_text('..lel')
    'from .. import lel'

    >>> path_to_import_text('.lul')
    'from . import lul'

    >>> path_to_import_text('lol')
    'import lol'

    >>> path_to_import_text('...na.na.na.na.na.na.Batman')
    'from ...na.na.na.na.na.na import Batman'

    >>> path_to_import_text('...........yolo.swagger')
    'from ...........yolo import swagger'

    :param path: The path to split.
    :type  path: str

    :return: The import text, like `from x import y` or `import z`
    :rtype: str
    """
    import_path, import_name = split_path(path)

    if import_path:
        return 'from {import_path} import {import_name}'.format(import_path=import_path, import_name=import_name)
    # end if
    return 'import {import_name}'.format(import_name=import_name)
# end def
