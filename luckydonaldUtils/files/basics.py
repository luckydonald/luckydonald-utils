# -*- coding: utf-8 -*-
import sys
import os
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)


def mkdir_p(path):
    """
    like mkdir -p
    Creates a folder with all the missing parent folders.
    """
    import errno
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
            # end try


# end def

"""
def open_folder(folder_path)
"""  # for different Platforms
if sys.platform == 'darwin':  # Mac OS
    logger.debug('platform "darwin", Mac OS X. Using `open` to open files/folders.')


    def open_folder(folder_path):
        """tries to open a folder in your system's browser"""
        import subprocess
        subprocess.check_call(['open', '--', folder_path])


    # end def

    def open_file_folder(file_path):
        """tries to open a folder, and select the given file in your system's browser"""
        import subprocess
        subprocess.check_call(['open', '-R', '--', file_path])
        # end def

elif sys.platform == 'linux2':  # linux, hopefully has gnome?
    logger.debug('platform "linux2", hopefully has gnome. Using `gnome-open` to open files/folders.')


    def open_folder(folder_path):
        """tries to open a folder in your system's browser"""
        import subprocess
        subprocess.check_call(['gnome-open', '--', folder_path])  # untested.


    # end def

    def open_file_folder(file_path):
        """tries to open a folder, and select the given file in your system's browser"""
        import subprocess
        open_folder(os.path.dirname(file_path))
        # end def
elif sys.platform == 'win32':  # windows
    logger.debug("platform win32, windows. Using `explorer` to open files/folders.")


    def open_folder(folder_path):
        """tries to open a folder in your system's browser"""
        import subprocess
        subprocess.check_call(['explorer', folder_path])


    # end def

    def open_file_folder(file_path):
        """tries to open a folder, and select the given file in your system's browser"""
        import subprocess
        try:
            subprocess.check_call(['explorer', '/select,"%s"' % file_path])
        except:
            open_folder(os.path.dirname(file_path))
            # end def
# end if
