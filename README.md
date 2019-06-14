# luckydonald-utils
###### A collection of utilities I use across different python projects.
[![Build Status](https://travis-ci.org/luckydonald/luckydonald-utils.svg?branch=master)](https://travis-ci.org/luckydonald/luckydonald-utils)
[![PyPI](https://img.shields.io/pypi/v/luckydonald-utils.svg)](https://pypi.python.org/pypi/luckydonald-utils)

[Documentation](#luckydonaldutils-documentation)

### Install    
`$` `pip install luckydonald-utils`    


### Update 
Via pip:
`$` `pip install --upgrade luckydonald-utils`    

Using the package:
`$` `python -m luckydonaldUtils.selfupdate`    

From python interpreter:
```python
from luckydonaldUtils import selfupdate
```

### Install from source
- Get the source
    - Download a release from [PyPi](https://pypi.python.org/pypi/luckydonald-utils) or [Github](https://github.com/luckydonald/python-utils/releases/),
    - or clone the latest code from Github:
    `$` `git clone https://github.com/luckydonald/luckydonald-utils.git && cd luckydonald-utils`    
- Navigate into the `luckydonaldUtils` folder and run 
    `$` `python setup.py install`

### Update from source
- If you manually downloaded your version, just follow the install steps again using a new version.
- If you cloned the code, navigate into the `luckydonaldUtils` folder and run 
    `$` `git pull && python setup.py install`
    

## ```luckydonaldUtils``` Documentation:
*(not a complete list)* 

#### ```clazzes```
Related to class manipulations.

- ```Singleton```: Metaclass to use, if only the one (the same) instance of a class is needed.  (Added in [v0.35](https://github.com/luckydonald/python-utils/releases/tag/v0.35))
- ```Kwags```: Extend and set `__FIELDS__ = tuple("a", "b", ...)` to be able to use `**obj`. ([v0.72](https://github.com/luckydonald/python-utils/releases/tag/v0.72)+)
    
    
#### ```djangos```
Utilities for django.

- ```csrf``` ([v0.22](https://github.com/luckydonald/python-utils/releases/tag/v0.22)-[27](https://github.com/luckydonald/python-utils/releases/tag/v0.27). Merged into ```djangos.requests``` in [v0.28](https://github.com/luckydonald/python-utils/releases/tag/v0.28))
- ```headers```  (added in [v0.23](https://github.com/luckydonald/python-utils/releases/tag/v0.23))
	- ```@header```: decorator to add/set a header. (added in [v0.24](https://github.com/luckydonald/python-utils/releases/tag/v0.24))     
		Use like ```@header('X-Important-Number', '4458')```
	- ```@headers```: decorator to set headers.    
		Use with an dict ```@headers({'X-Powered-By': 'Magical Unicorns', 'X-Foo': 'Bar!'})``` or as kwargs```@headers(X_Powered_By="Magical Unicorns", X_Foo="Bar!")```
	- ```@easteregg_headers```: Adds my favorite collection of easter egg headers.    
- ```responses``` (added in [v0.25](https://github.com/luckydonald/python-utils/releases/tag/v0.25))    
	- ```json_response(status=None, statusText=None, exception=None, content=None)```:    
		Easier json Responses, also given Exception is rendered as json too.
	- ```@catch_exception```: ([v0.26](https://github.com/luckydonald/python-utils/releases/tag/v0.26) only)    
		With [v0.27](https://github.com/luckydonald/python-utils/releases/tag/v0.27), use ```@render_all_exceptions```, ```@render_DoOutputException```
		or ```@render_specific_exception(exception_class, exception_render_func=None)```.    			
	- ```@render_all_exceptions```: ([v0.27](https://github.com/luckydonald/python-utils/releases/tag/v0.27)+)    
		Catches all exceptions and renders the exception ```e``` as ```HttpResponse(str(e), status=500)```.
	- ```@render_DoOutputException```: ([v0.27](https://github.com/luckydonald/python-utils/releases/tag/v0.27)+)    
		Like ```@render_all_exceptions```, but only renders a DoOutputException. Useful if something deep in the call stack want to fail with a message.
	- ```@render_specific_exception(exception_class, exception_render_func=None)```: ([v0.27](https://github.com/luckydonald/python-utils/releases/tag/v0.27)+)    
		Like ```@render_DoOutputException```, but you can specify the Exception you are expecting.      
		Also you can optionally set a function to render that exception instead of using the default    
		```    
		def render(response, e):
			return HttpResponse(str(e), status=500)
		```
- ```requests``` ([v0.28](https://github.com/luckydonald/python-utils/releases/tag/v0.28)+)
	- ```check_csrf(request)```: Manually checks the csrf. Returns ```True``` or ```False```. (moved here in [v0.28](https://github.com/luckydonald/python-utils/releases/tag/v0.28))    
	- ```GET_to_bool(request, key)```: Parses a GET parameter in the request as bool. ```"true"``` becomes ```True```, ```"false"``` becomes ```False```, ```"null"``` becomes ```None```.
- ```middelware``` a collection.
	- ```access```:
		- ```AllowFromIPMiddleware```: [v0.31](https://github.com/luckydonald/python-utils/releases/tag/v0.31)+    
			Allow only given IPs to access, else raises a `Http404` error. Is will be ignored when `DEBUG` is `True`, or `settings.ALLOW_FROM` is `None`.    
			Set in the *settings.py* file: ```ALLOW_FROM = ["134.169.0.0/16"]```    
			Include in your ```MIDDLEWARE_CLASSES```: ```"luckydonaldUtils.djangos.middleware.access.AllowFromIPMiddleware"```
	- ```header```:
		- ```EastereggHeadersMiddleware```: [v0.34](https://github.com/luckydonald/python-utils/releases/tag/v0.34)    
			Sets some funny headers.    
			Include in your ```MIDDLEWARE_CLASSES```: ```"luckydonaldUtils.djangos.middleware.headers.EastereggHeadersMiddleware"```
#### ```exceptions```
Exception related stuff.

- ```assert_type_or_raise(value, expected_type_clazz_or_tuple, *more_clazzes, exception_clazz=TypeError, parameter_name=None)```: Since <sup>[2](#2)</sup> [v0.53](https://github.com/luckydonald/python-utils/releases/tag/v0.53); Added `parameter_name` parameter in [v54](https://github.com/luckydonald/python-utils/releases/tag/v54).
    A better `assert(isinstance(a, B)` because it supports `None` (as well as some other types except tuple or list), and an nice exception text.


#### ```files```
Collection of things which are file related.
(This structure exists since [v0.47](https://github.com/luckydonald/python-utils/releases/tag/v0.47))

- `files.basics` [v0.47](https://github.com/luckydonald/python-utils/releases/tag/v0.47)+
    - `mkdir_p(path)` like `mkdir -p` [v0.43](https://github.com/luckydonald/python-utils/releases/tag/v0.43)
    - `open_folder(folder_path)` tries to open a folder in your system's browser
    - `open_file_folder(file_path)` tries to open a folder, and select the given file in your system's browser
- `files.mime` [v0.47](https://github.com/luckydonald/python-utils/releases/tag/v0.47)+
    - `guess_extension(mime)` Shortcut for getting extension to a given mime string.
    - `get_file_mime(file_path=None, file_url=None)` Shortcut to get the mime from either
    - `get_byte_mime(bytes)` Shortcut to get a mime from bytes in a variable.
    - `get_file_suffix(file_path=None, file_url=None)` This calls `get_file_mime()` to get the mime, and then calls `guess_extension()`.
- `files.name` [v0.47](https://github.com/luckydonald/python-utils/releases/tag/v0.47)+
    - `do_a_filename(input_file_name)` Bad attempt to make file names better, by replacing some characters. This is no escaping.
- `files.temp` [v0.47](https://github.com/luckydonald/python-utils/releases/tag/v0.47)+
    - `gettempdir(temp_folder_name="luckydonald-utils")` Gets/creates a folder in the temporary files of the system.
- `files.tree` [v0.47](https://github.com/luckydonald/python-utils/releases/tag/v0.47)+
    - `tree(directory, padding="", print_files=False, level=-1, print_it=True)` (New in [v0.47](https://github.com/luckydonald/python-utils/releases/tag/v0.47))

#### ```flasks```
Utilities for flask.
[v0.59](https://github.com/luckydonald/python-utils/releases/tag/v0.59)+

- `flasks.routing`
    - `route_for`: Basically `flask.url_for` in reverse. You give a url, it gives you the route and the required arguments.
    - `get_safe_next`: Checks if the specified `url` in like a `?next=<url>` parameter is part of our registered routes, and thus seems safe to redirect to.
- `flasks.launcher`
    - `Launcher`: Allow `flask`'s auto-reload to survive syntax errors and similar exceptions, also show them in the browser.

#### ```jinja2```
Utilities for the jinja templating engine.
[v0.64](https://github.com/luckydonald/python-utils/releases/tag/v0.64)+

- `filters`: Filter for templates.
    - `br`: Add `<br>` to linebreaks.

#### ```functions```
Information about calling functions (Added in [v0.35](https://github.com/luckydonald/python-utils/releases/tag/v0.35))

- ```@caller```: Functions decorated with this will be called with an `call` kwarg, containing information about the function itself, and the caller.
    If the caller could not be fetched correctly, the `caller`s attributes all will be `None`.

- ```@cached```: [v0.49](https://github.com/luckydonald/python-utils/releases/tag/v0.49) Decorator to cache function return values (based on *args and **kwargs). You can specify a `datetime.timedelta` in `max_age` after which that function will be called again.
 
- ```@deprecated```: Decorator to mark functions as deprecated. 
    A warning will be logged when the function is used. 
    With [v0.47](https://github.com/luckydonald/python-utils/releases/tag/v0.47) you can specify a message.
    ```python
    @deprecated("Reason goes here")
    def foo():
        pass
    ```

- ```@gone```: Decorator to mark functions as gone. 
    A NotImplementedError will be emitted when the function is used.
 
#### ```holder```
###### (Added in [v0.45](https://github.com/luckydonald/python-utils/releases/tag/v0.45))
Caches a result, and returns it. Useful in if statements.

In python it is not possible to store the result of an expression in a variable while being inside of an `if`:

```python
if (temp=do_something()) == 42:
    foo(temp)
```

And storing it before is not an option?
(you have a very resources-expensive call, or changing values, or are in an `elif`)

```python
temp = do_something()
temp2 = do_something_else()
if temp == 42:
    foo(temp)
elif temp2:
    foo2(temp2)
```

Somebody need to **hold** that result for you:

```python
from luckydonaldUtils.holder import Holder
h = Holder()
if h(do_something()) == 42:
    foo(h())
elif h(do_something_else()):
    foo2(h())
```
That's what `Holder` is for.

#### ```iterators```
All stuff related to list and iterators. 

- ~~```iter_with_i (iterator, start_i=0)```~~: (Added in [v0.34](https://github.com/luckydonald/python-utils/releases/tag/v0.34)) Deprecated since [v0.73](https://github.com/luckydonald/python-utils/releases/tag/v0.73).     
	Yields a tuple of the iterator result and an integer incrementing each time.    
	```
	for iterator_result, i in iter_with_i(["a","b"])
	```
- ```chunks(iterable, size)```: ([v0.73](https://github.com/luckydonald/python-utils/releases/tag/v0.73)+)    
    Yields chunks of an `iterable`, using the `slice` protocol. That means, the slices are resolved lazy when needed and thus generated, and not loaded up front. End is determined by the actual length of a chunk being less then the specified `size`.
- ```chunks_known_length(iterable, size, length=None)```: ([v0.73](https://github.com/luckydonald/python-utils/releases/tag/v0.73)+)
    Similar to `chunks(...)` but uses a for loop with a previously determined max length to do the slicing, instead of the `while True` `if len < size: break` loop.

#### ```interactions```
Interact with the user.

- ```safe_eval (user_input, no_builtins_object=NoBuiltins(eval_safe_builtin_list, eval_safe_builtin_mapping))```: (Added in [v0.37](https://github.com/luckydonald/python-utils/releases/tag/v0.37))   
    Tries to make a safe execution of user inputted python code. Per default uses a `interactions.NoBuiltins` object
    with `interactions.eval_safe_builtin_list` as allowed commands.
     - `user_input`: the string
     - `no_builtins_object`: a `NoBuiltins` object, initialized with `interactions.eval_safe_builtin_list`

- ```NoBuiltins (allowed_builtins, allowed_functions=None, allowed_vars=None)```: (Added in [v0.37](https://github.com/luckydonald/python-utils/releases/tag/v0.37))   
    Used to allow custom variables.
     - `allowed_builtins`: List of allowed buildins (strings)
     - `allowed_functions`: Dict with names of functions and the functions to be called.
     - `allowed_vars`: Given variables. A Mapping with a dict.
    
- ```eval_safe_builtin_list```: (Added in [v0.37](https://github.com/luckydonald/python-utils/releases/tag/v0.37))   
    A default list of builtin commands/variables considered 'safe'.
   
- ```eval_safe_builtin_mapping```: (Added in [v0.37](https://github.com/luckydonald/python-utils/releases/tag/v0.37))   
    A default list of builtin functions/variables, which are not at `__builtin__`s root level, but mapped as if.
    They are mathematical functions considered 'safe'.


#### ```network```
-  ```ip```: Tools for ip addresses
	- ```binary_ip_to_str(host)```: converts the binary ip to a string.
- ```mod_wsgi```
	-	```reloader```: Auto reloading capabilities for **mod_wsgi** environments. ([v0.28](https://github.com/luckydonald/python-utils/releases/tag/v0.28)+)    

#### ```regex```
Package of some regular expressions I found useful.

- ```github```
    - ```REPO_NAME_REGEX```: Repo name validation. (Since<sup>[1](#1)</sup> [v0.40](https://github.com/luckydonald/python-utils/releases/tag/v0.40))
    - ```AT_USERNAME_REGEX```: Searches @usernames.  (Since [v0.40](https://github.com/luckydonald/python-utils/releases/tag/v0.40); added match group `user` in [v0.41](https://github.com/luckydonald/python-utils/releases/tag/v0.41))
    - ```FILE_URL_REGEX```: Matches github urls pointing to files or directories.(Since<sup>[1](#1)</sup> [v0.40](https://github.com/luckydonald/python-utils/releases/tag/v0.40); added match group `protocol` in [v54](https://github.com/luckydonald/python-utils/releases/tag/v54))
    - ```SIMPLE_URL_REGEX```: Matches github urls. (Added in [v0.54](https://github.com/luckydonald/python-utils/releases/tag/v0.54)+)
    Matching groups:
        - url: the complete url
            - protocol: `'https://'` or `'http://'` or empty/non-existent
            - user: git user or organisation
            - repo: the repository
            - path: When existent, this is not the project page (root of master)
                - kind: blob or tree
                - branch: the name of the branch (kind=tree), or the commit hash (kind=blob)
            - file: the rest of the filepath (from root of that branch, can be empty)
        - hash: Can be non-existent or empty. Everything behind the '#'
- ```url```
    - ```URL_REGEX```: Matching URLs. Based on [dperini's MIT licensed Gist](https://gist.github.com/dperini/729294#gistcomment-1296121) (Added in [v0.58](https://github.com/luckydonald/python-utils/releases/tag/v0.58))
    - ```youtube```:
        - ```YOUTUBE_REGEX```: Matches youtube videos. The matching group `vid` contains the video id.
    
#### ```tg_bots```
Utilities for the telegram bots (pytgbot and/or teleflask).
- `gitinfo`: Parse git meta information written by a deploy script.
- `language`: Helper for loading language files (classes). [v0.64](https://github.com/luckydonald/python-utils/releases/tag/v0.64)+
- `peer`: Tools for handling chats and users.  [v0.74](https://github.com/luckydonald/python-utils/releases/tag/v0.74)+
    - `chat`:  Tools for chats.
        - `format`: Formatting related chat tools.
            - `format_chat(chat: Chat)`: Formats a channel for html, escaping username and title.
    - `user`:  Tools for chats.
        - `format`: Formatting related chat tools.
            - `format_user(user: User, ...)`: Formats a user for html, escaping html tags where needed.
            - `retrieve_and_format_user(user_id, ...)`: Retrieves a user from telegram, and formats it with `format_user(...)`.
        - `rights`: User permission related tools.
            - `is_admin(...)`: Checks if a user has admin privileges, and optionally a specified right.
            - `retrieve_and_is_admin(...)`: Retrieves info about a user in a chat from telegram, and calls `is_admin(...)`.  


#### ```text```

String manipulation, etc.

- `split_in_parts(string, parts, strict=False)`: [v0.48](https://github.com/luckydonald/python-utils/releases/tag/v0.48)+  Splits a string in given `parts` pieces.

#### ```typing```

Additions to the great stuff in the `typing` module. Python 3+ it seems.
- `JSONType`: The stuff returned by `json.loads(str)`. [v0.73](https://github.com/luckydonald/python-utils/releases/tag/v0.72)+  

#### ```compat```  [v0.58](https://github.com/luckydonald/python-utils/releases/tag/v0.58)

Detecting versions and stuff. For string compatibility use `.encoding`.

- ```py2```: `True` if is python 2, `False` otherwise.
- ```py3```: `True` if is python 3, `False` otherwise.


    
#### ```webserver```
(added in [v0.20](https://github.com/luckydonald/python-utils/releases/tag/v0.20))    

- class ```BetterHTTPRequestHandler```
	- Like the [```BaseHTTPRequestHandler```](https://docs.python.org/2/library/basehttpserver.html), but without output to ```stderr```, *(why would anyone do that?!?)*. Instead it goes to loggers. Also some helpfull things.
	- Changed to use [logging](https://docs.python.org/3/library/logging.html)
		- ```log_message``` now uses ```logger.info```
		- ```log_request``` writes to ```logger.debug```, to not spam you on every request.
		- ```log_error``` uses ```logger.error```
	- Added a ```write_text(self, msg, content_type="text/plain", is_binary=False)``` function to make answering with text/data easy.
		- ```msg```: The text to send to the browser/client.
		- *```content_type```: Optional.* If you don't like it to be text, change that here.
		- *```is_binary```: Optional.* Text (unicode) needs to be converted to binary. If you already have binary (e.g. an PNG as binary data) you can set that here.
		- returns nothing.
	- Modified ```translate_path```: Now accepts local fitting paths automatically,
	e.g. "/path/to/www-dir/foo.png" is valid if that folder exists. Now it won't change the path to "/path/to/www-dir/foo.png/path/to/www-dir/foo.png", like it did before.
	- Added a ```parse_POST``` function to get the post request's data fields returned.	
- ```start_a_webserver(handler, port, host="")```. 	Starts a ```HTTPServer```, using the given ```handler```.
	- ```handler```: An handler instance, e.g. an ```BetterHTTPRequestHandler```
	- ```port```: The port where to serve on. For example ```80``` or ```8080``` for HTTP (```80``` often needs root privileges).
	- *```host```: Optional.* A host where to serve on. If an empty string ```""``` (default) is given, all incoming connections are allowed. (you can connect from localhost, from lan, from internet, etc.)
	- returns: The ```HTTPServer``` created.
	

<hr>

#### Notes

1. <a name="1">*`regex.github.REPO_NAME_REGEX` and `regex.github.FILE_URL_REGEX` where already present in [v0.38](https://github.com/luckydonald/python-utils/releases/tag/v0.38) as `regex.urls.github.REPO_NAME_REGEX` and `regex.urls.github.GITHUB_FILE_REGEX`.*</a>
2. <a name="2">*`exceptions.assert_type_or_raise` was already present in [v0.46](https://github.com/luckydonald/python-utils/releases/tag/v0.46) as `exceptions.assert_or_raise`.*</a>
3. <a name="3">**</a>
