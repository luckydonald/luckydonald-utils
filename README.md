# python-utils
###### A collection of utilities I use across different python projects.

Install with pip:
```shell
pip install luckydonald-utils
```    
 

(Released on [PyPI](https://pypi.python.org/pypi/luckydonald-utils) [(Github mirror)](https://github.com/luckydonald/python-utils/releases/))

### Documentation:
*(not a complete list)*
####```luckydonaldUtils```
- ```webserver``` (added in [v0.20](https://github.com/luckydonald/python-utils/releases/tag/v0.20))
	- ```BetterHTTPRequestHandler```
		- Like the ```BaseHTTPRequestHandler```, but without output to ```stderr```, *(why would you do that?!?)*. Instead it goes to loggers.
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
	
	- ```start_a_webserver(handler, port, host="")```. 	Starts a ```TCPServer```, using the given ```handler```.
		- ```handler```: An handler instance, e.g. an ```BetterHTTPRequestHandler```
		- ```port```: The port where to serve on. For example ```80``` or ```8080``` for HTTP (```80``` often needs root privileges).
		- *```host```: Optional.* A host where to serve on. If an empty string ```""``` (default) is given, all incoming connections are allowed. (from localhost, from lan, from internet, etc.)
		- returns: The ```TCPServer``` created.