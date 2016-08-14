Changelog
=========
0.47
----
- Restructured `files.py` into a cleaner structured module.
    - `files.basics`
        - `mkdir_p`
        - `open_folder`
        - `open_file_folder`
    - `files.mime`
        - `guess_extension`
        - `get_file_mime`
        - `get_byte_mime`
        - `get_file_suffix`
    - `files.name`
        - `do_a_filename`
    - `files.temp`
        - `gettempdir`
- Newly added `files.tree.tree(directory, padding="", print_files=False, level=-1, print_it=True)`. 
    It comes executable from command line. Just call `python -m luckydonaldUtils.files.tree` 
- Improved `functions.deprecated` to now also accept a message:
    ```python
    @deprecated("Reason goes here")
    def foo():
        pass
    ```

0.46
----
- Fixed selfupdate. Closes [#5](https://github.com/luckydonald/luckydonald-utils/issues/5).
- Added `luckydonaldUtils.exceptions.assert_or_raise(...)`


0.45
----

- Added [`luckydonaldUtils.holder.Holder`](README.md#holder).

before
------
No changelog was made.
Either look into the commit history, or have a look at the `README.md`, it comes with version information too.

