PickleParser
============

A package used for getting a preview object for pickle string.

[![Build Status](https://travis-ci.org/tumb1er/pickleparser.svg)](https://travis-ci.org/tumb1er/pickleparser)

Example of a problem
--------------------

One of your services raises an exception:

```python

raise django.core.exceptions.ValidationError("error")
```

This exception is pickled to a string as a result of RPC call.
If RPC client has Django installed, it's OK. 
But if you have a monitoring service without django, you'll get a big problem.

```python

>>> pickle.loads(rpc_result)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/local/lib/python2.7/pickle.py", line 1382, in loads
    return Unpickler(file).load()
  File "/usr/local/lib/python2.7/pickle.py", line 858, in load
    dispatch[key](self)
  File "/usr/local/lib/python2.7/pickle.py", line 1090, in load_global
    klass = self.find_class(module, name)
  File "/usr/local/lib/python2.7/pickle.py", line 1124, in find_class
    __import__(module)
ImportError: No module named django.core.exceptions

```

**pickleparser** is attended to solve this issue and allow editing of these 
pickled messages:

```python
>>> import pickleparser
>>> with pickleparser.StubContext():
...   data = pickleparser.unpickle(rpc_result)
...   print(data['error'])
...   data['result'] = 'success'
...   patched = pickle.dumps(data)
... 
<django.core.exceptions.ValidationError object at 0x7f92f52018d0>

```




