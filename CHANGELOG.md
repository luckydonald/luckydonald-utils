Changelog
=========
0.54 (not released yet)
----
- Added optional `parameter_name` to `assert_type_or_raise`.
- Added `lcut` and `rcut`, fixed `split_in_parts`.
- Updated related tests. Full test coverage for those.

0.53
----
- Added methods in `luckydonaldUtils.interactions` to see if a string is `True` or `False`
    - `def string_is_yes(...)`: checks for a true-ish value and return `False` otherwise
    -  and `def string_y_n(...)`: expects y/n (case insensitive)
- Renamed `def assert_or_raise(...)` to `def assert_type_or_raise(...)` in  `luckydonaldUtils.exceptions` (the old name as an alias to keep backwards compatibility, but it will warn you every time)

0.52
----
From Bonbot:
- added `def cut_paragraphs(...)`: cut text down to a specified lenght. 

0.51
----
Logger update:
- `def add_colored_handler(...)`: added `filter` parameter. It will be applied to the handler.
- `def test_logger_levels(...)`: 
    - added `name` parameter to test with a name other then that function.
    - added `force_all_levels` parameter to test with setting the logger to `DEBUG` level first.
- `def getLoglevelInt(...)`: Now allows you to input numbers, too (both as str or as int).
- `def getLoglevelInt(...)`: Now allows you to input numbers, too (both as str or as int).
- New `class LevelByNameFilter`: You can specify the names and set levels of files you want to log.

0.50
----
- Bugfix: Fixed `@cached` decorator, to work with non jsonable cases, like the`self` attribute in classes. Should be more reliable overall.
 
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

