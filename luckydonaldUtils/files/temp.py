import errno
import os
import tempfile


def gettempdir(temp_folder_name="luckydonald-utils"):
    """gets or creates a folder in the temporary files of the system."""
    temp_dir = tempfile.gettempdir()
    temp_dir = os.path.join(temp_dir, temp_folder_name)
    # py3
    # os.makedirs(temp_dir, exist_ok=True)  # don't raise errors if existent.
    # py2/3 exist_ok workaround
    try:
        os.makedirs(temp_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:  # don't raise errors if existent.
            raise
    # end exist_ok workaround
    return temp_dir
