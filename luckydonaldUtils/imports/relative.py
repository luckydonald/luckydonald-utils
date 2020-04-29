#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

"""
package/            # package
    __init__.py     # package
    subpackage1/    # package.subpackage1
        __init__.py # package.subpackage1
        moduleX.py  # package.subpackage1.moduleX
        moduleY.py  # package.subpackage1.moduleY
    subpackage2/    # package.subpackage2
        __init__.py # package.subpackage2
        moduleZ.py  # package.subpackage2.moduleZ
    moduleA.py      # moduleA

Assuming that the current file is either moduleX.py or subpackage1/__init__.py, following are correct usages of the new syntax:
package.subpackage1.moduleX


# from .moduleY import spam
assert relimport('package.subpackage1.moduleY.spam', 'package.subpackage1.moduleX') == '.moduleY.spam'

# from . import moduleY
assert relimport('package.subpackage1.moduleY', 'package.subpackage1.moduleX') == '.moduleY'

# from ..subpackage1 import moduleY
assert relimport('package.subpackage1.moduleY', 'package.subpackage1.moduleX') == '..subpackage1.moduleY'

# from ..subpackage2.moduleZ import eggs
assert relimport('package.subpackage2.moduleZ', 'package.subpackage1.moduleX') == '..subpackage2.moduleZ.eggs'

# from ..moduleA import foo
assert relimport('moduleA.foo', 'package.subpackage1.moduleX') == '..moduleA.foo'

# from ...package import bar
assert relimport('package.bar', 'package.subpackage1.moduleX') == '..package.bar'

# from ...sys import path
assert relimport('sys.path', 'package.subpackage1.moduleX') == '..sys.path'

assert relimport('foo.bar.batz', 'foo.bar') == '.batz'

"""


def relimport(path, start):
    """
    Return a relative import path from the `start` module's view'.
    This is a path computation: the filesystem is not accessed to confirm the existence or nature of `destination` or `start`.

    :param path: the destination path
    :type  path: str

    :param start: our current module where we call the import. You can supply the current module with `start=__NAME__`.
    :type  start: str

    :return: the relative path. `'...foo.bar'`
    :rtype: str
    """
    path_parts = path.split('.')
    start_parts = start.split('.')
    original_path_parts = path.split('.')

    for i in range(min(len(start_parts), len(path_parts))):
        if start_parts[0] == path_parts[0]:
            start_parts.pop(0)
            path_parts.pop(0)
            continue
        else:
            break
        # end if
    # end for
    if path_parts == [] and start_parts == []:
        # same path
        # a.b.c == a.b.c
        return None  # same dir
    # end if
    if start_parts == [] and path_parts:
        # some children module, even deeper in the tree
        # a == a.b.c
        return "." + ".".join(path_parts)
    # end if
    if start_parts and path_parts == []:
        # some parent folder module
        # a.b.c == a
        # make sure it's ending with a package name to import.
        return '.' + "." * len(start_parts) + '.' + original_path_parts[-1]
    # end if
    if start_parts and path_parts:
        # so the paths differ at some point, or from the beginning.
        # a.b.c == x.y.z
        return '.' + "."*(len(start_parts)-1) + ".".join(path_parts)
    # end if
# end def


gnerf = relimport('foo.bar.batz', start='foo.bar')  # in foo.bar: from . import batz: .batz
assert gnerf == '.batz'

gnerf = relimport('foo.bar.batz.gneeh', start='foo.bar')
assert gnerf == '.batz.gneeh'

gnerf = relimport('foo.bar', start='foo.bar.batz')  # in foo.bar.batz: from ... import batz
# assert gnerf == '..'
assert gnerf == '...bar'

gnerf = relimport('foo.bar', start='foo.bar.batz.gneeh')  # in foo.bar: from . import batz: .batz
# assert gnerf == '...'
assert gnerf == '....bar'

gnerf = relimport('foo.bar.c', start='foo.bar.batz')
assert gnerf == '.c'

gnerf = relimport('foo.b.c', start='foo.bar.batz')
assert gnerf == '..b.c'

gnerf = relimport('package.subpackage1.moduleY.spam', start='package.subpackage1.moduleX')
assert gnerf == '.moduleY.spam'

gnerf = relimport('package.subpackage1.moduleY', start='package.subpackage1.moduleX')
assert gnerf == '.moduleY'

gnerf = relimport('package.subpackage2.moduleZ.eggs', start='package.subpackage1.moduleX')
assert gnerf == '..subpackage2.moduleZ.eggs'

gnerf = relimport('moduleA.foo', start='package.subpackage1.moduleX')
assert gnerf == '...moduleA.foo'

gnerf = relimport('sys.path', start='package.subpackage1.moduleX')
assert gnerf == '...sys.path'

gnerf = relimport('foo.bar.batz', start='foo.bar')
assert gnerf == '.batz'
