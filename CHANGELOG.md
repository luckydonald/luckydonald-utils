Changelog
=========
0.49
----
- Added `@cached(max_age=None)` decorator.
- Also decorators can be accessed form the `.decorators` import

0.48
----
- Improvements in `tree`, and `dependencies`.
- Added `text.split_in_parts(string, parts, strict=False)`: Splits a string in given `parts` pieces.

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
    - 
- Newly added `files.tree.tree(directory, padding="", print_files=False, level=-1, print_it=True)`. 
    It comes executable from command line. Just call `python -m luckydonaldUtils.files.tree` 
- Improved `functions.deprecated` to now also accept a message:
    ```python
    @deprecated("Reason goes here")
    def foo():
        pass
    ```
- Cleaned up imports.
    - Also there now is a `dependencies-full.txt` file, listing all dependencies which might be needed.
        Should now be a complete list.
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

