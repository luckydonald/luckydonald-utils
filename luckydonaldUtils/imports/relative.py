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


def relimport(destination, start):
    """
    Return a relative import path from the `start` module's view'.
    This is a path computation: the filesystem is not accessed to confirm the existence or nature of `destination` or `start`.

    Here are some examples:

        >>> relimport(destination='foo.bar.batz', start='foo.bar')  # in foo.bar: from . import batz: .batz
        '.batz'

        >>> relimport(destination='foo.bar.batz.gneeh', start='foo.bar')
        '.batz.gneeh'

        >>> relimport(destination='foo.bar', start='foo.bar.batz')  # in foo.bar.batz: from ... import batz
        '...bar'

        >>> relimport(destination='foo.bar', start='foo.bar.batz.gneeh')  # in foo.bar: from . import batz: .batz
        '....bar'

        >>> relimport(destination='foo.bar.c', start='foo.bar.batz')
        '.c'

        >>> relimport(destination='foo.b.c', start='foo.bar.batz')
        '..b.c'

        >>> relimport(destination='package.subpackage1.moduleY.spam', start='package.subpackage1.moduleX')
        '.moduleY.spam'

        >>> relimport(destination='package.subpackage1.moduleY', start='package.subpackage1.moduleX')
        '.moduleY'

        >>> relimport(destination='package.subpackage2.moduleZ.eggs', start='package.subpackage1.moduleX')
        '..subpackage2.moduleZ.eggs'

        >>> relimport(destination='moduleA.foo', start='package.subpackage1.moduleX')
        '...moduleA.foo'

        >>> relimport(destination='sys.path', start='package.subpackage1.moduleX')
        '...sys.path'

        >>> relimport(destination='foo.bar.batz', start='foo.bar')
        '.batz'

        >>> relimport(destination='foo.bar.batz.Something', start='foo.bar.gnerf')
        '.batz.Something'

    Note: Those examples above are also used as part of the unit tests, via the doctest system.
    Note: This is called the same way as `os.path.relpath(path, start)` would be, and is compatible in calling,
          except the `path` parameter called `destination` to be more clear, and `start` (not yet) being optional.

    :param destination: the destination path
    :type  destination: str

    :param start: our current module where we call the import. You can supply the current module with `start=__NAME__`.
    :type  start: str

    :return: the relative path. `'...foo.bar'`
    :rtype: str
    """
    destination_parts = destination.split('.')
    start_parts = start.split('.')
    original_destination_parts = destination.split('.')

    for i in range(min(len(start_parts), len(destination_parts))):
        if start_parts[0] == destination_parts[0]:
            start_parts.pop(0)
            destination_parts.pop(0)
            continue
        else:
            break
        # end if
    # end for
    if destination_parts == [] and start_parts == []:
        # same path
        # a.b.c == a.b.c
        return None  # same dir
    # end if
    if start_parts == [] and destination_parts:
        # some children module, even deeper in the tree
        # a == a.b.c
        return "." + ".".join(destination_parts)
    # end if
    if start_parts and destination_parts == []:
        # some parent folder module
        # a.b.c == a
        # make sure it's ending with a package name to import.
        return '.' + "." * len(start_parts) + '.' + original_destination_parts[-1]
    # end if
    if start_parts and destination_parts:
        # so the paths differ at some point, or from the beginning.
        # a.b.c == x.y.z
        return '.' + "."*(len(start_parts)-1) + ".".join(destination_parts)
    # end if
# end def
