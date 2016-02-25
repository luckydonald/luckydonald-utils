"""
    Only one Instance of the class.
    Like in Java .getInstance()

    Python 3:
    apply with keyword argument in the base-class list:
    >>> class Exampe(object, metaclass = Singleton):
    >>>    pass

    Python 2.7:
    apply like
    >>> class Exampe(object):
    >>>    __metaclass__ = Singleton
    >>>    pass

"""


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
