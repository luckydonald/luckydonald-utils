# python-utils
###### A collection of utilities I use across different python projects.

Install with pip:
```shell
pip install luckydonald-utils
```    
 

(Released on [PyPI](https://pypi.python.org/pypi/luckydonald-utils) [(Github mirror)](https://github.com/luckydonald/python-utils/releases/))

## ```luckydonaldUtils``` Documentation:
*(not a complete list)* 

#### ```clazzes```
Related to class manipulations. (Added in [v0.35](https://github.com/luckydonald/python-utils/releases/tag/v0.35))

- ```Singleton```: Metaclass to use, if only the one (the same) instance of a class is needed.
    
    
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

#### ```functions```
Information about calling functions (Added in [v0.35](https://github.com/luckydonald/python-utils/releases/tag/v0.35))

- ```@caller```: Functions decorated with this will be called with an `call` kwarg, containing information about the function itself, and the caller.
    If the caller could not be fetched correctly, the `caller`s attributes all will be `None`.

- ```@deprecated```: Decorator to mark functions as deprecated. 
    A warning will be logged when the function is used.

- ```@gone```: Decorator to mark functions as gone. 
    A NotImplementedError will be emitted when the function is used.
    

#### ```iterators```
All stuff related to list and iterators. 

- ```iter_with_i(iterator, start_i=0)```: (Added in [v0.34](https://github.com/luckydonald/python-utils/releases/tag/v0.34))    
	Yields a tuple of the iterator result and an integer incrementing each time.    
	```
	for iterator_result, i in iter_with_i(["a","b"])
	```

#### ```network```
-  ```ip```: Tools for ip addresses
	- ```binary_ip_to_str(host)```: converts the binary ip to a string.
- ```mod_wsgi```
	-	```reloader```: Auto reloading capabilities for **mod_wsgi** environments. ([v0.28](https://github.com/luckydonald/python-utils/releases/tag/v0.28)+)    


#### ```webserver```
(added in [v0.20](https://github.com/luckydonald/python-utils/releases/tag/v0.20))    

- class ```BetterHTTPRequestHandler```
	- Like the ```BaseHTTPRequestHandler```, but without output to ```stderr```, *(why would anyone do that?!?)*. Instead it goes to loggers.
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
	
