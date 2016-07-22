"""
Caches a result, and is able to return it. Useful in if statements.

In python it is not possible to store the result of an expression in a variable while being inside of an if:

.. code:: python

| if temp=do_something() == 42:
|   foo(temp)


And storing it before is not an option?
(you have something very resources-expensive, or changing values)

.. code:: python

| temp = do_something()
| temp2 = do_something_else()
| if temp == 42:
|   foo(temp)
| elif temp2:
|   foo2(temp2)


Somebody need to hold that result for you:

.. code:: python

| h = Holder()
| if h(do_something()) == 42:
|   foo(h())
| elif h(do_something_else()):
|   foo2(h())

That's what `Holder` is for.
"""


class Holder(object):
    value = None

    def set(self, value):
        self.value = value
        return value

    def get(self):
        return self.value

    def call(self, *args, **kwargs):
        if len(args) == 0 and len(kwargs) == 0:
            return self.get()
        else:
            return self.set(*args, **kwargs)

    def to_string(self):
        return str(self.value)

    def to_verbose_string(self):
        return repr(self.value)

    def not_empty(self):
        return True if self.value else False

    # holder = utils.Holder();
    __call__ = call  # holder("test")
    __get__ = get  # print(holder)
    __set__ = set  # holder = "test"
    __bool__ = not_empty  # if holder:
    __str__ = to_string  # user output
    __repr__ = to_verbose_string  # debug output
