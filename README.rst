=============
Lamia
=============
:Author:	Jun Kimura
:Licence: 	MIT
:Description:	Cache module for python.

Require
-----------
::

 Python2.x>=2.6
 
Install
------------
::

 python setup.py install

Usage
------------
::

	>>> from Lamia.cache import Cache
	
	# Cache class's "__init__" method create a directory which store the cache-file.
	>>> cache = Cache(cache_root="/tmp/lamia", 
	... default_expires=10, 
	... namespace="test")
	...
	>>> cache.store("a_key", "value") # equal=>` cache["a_key"] = "value" `
	>>> cache["a_key"]
	"value"
	
	# This method store "value" in cache-file if user specify bool-value for "is_store_file".   
	>>> cache.store("b_key", "value",is_store_file=True)
	
	# Lamia serve a decorator to cache fetched data from function in memory and file.
	>>> cached = cache.cache_decorator
	>>> @cached(expires=100, is_store_file=False)
	... def get_any_value(arg):
	...     return "arg is %s" % str(arg)
	...
	>>> get_any_value("one")
	"arg is one"
	
	# Create another cache-file if specify different argument for Cached function. 
	>>> get_any_value("two")
	"arg is two"
	
	# Lamia servre a method to delete the old cache from directory.
	>>> cache.purge()
	
	
	# Async mode
	
	>>> cache.save(is_async=True)
	>>> cache.async_loop()
	
	>>> cache.purge(is_async=True)
	>>> cache.async_loop() 
	
	
