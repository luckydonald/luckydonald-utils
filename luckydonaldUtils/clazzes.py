"""
    Only one Instance of the class.
    Like in Java .getInstance()


    Make a class Singleton:

    Python 3:
    apply with keyword argument in the base-class list:
    >>> class Example(object, metaclass = Singleton):
    >>>    pass

    Python 2.7:
    apply like
    >>> class Exampe(object):
    >>>    __metaclass__ = Singleton
    >>>    pass


    Usage of the class:

    At the first call you have to supply the parameters for class, as usual.
    Afterwards you can omit them, they will be ignored if given.

    Create the instance:
    >>> whatever = Example("arguments", "go", "here", as_well_as="keyword args")

    Use a already created instance:
    >>> something = Example()  # note: No args or kwargs required here.
"""


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            args = args if args else []
            kwargs = kwargs if kwargs else {}
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
        # end def
