try:
    from collections.abc import Mapping  # py3
except ImportError:
    from collections import Mapping  # py2
# end try


class Singleton(type):
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
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            args = args if args else []
            kwargs = kwargs if kwargs else {}
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    # end def
# end class


class Kwargs(Mapping):
    __FIELDS__ = tuple()

    def __getitem__(self, parameter):
        """
        Retrieve an object variable
        :param parameter: The current class's parameter to retrieve.
        :raises KeyError: Key not found.
        :return:
        """
        if parameter in self.__FIELDS__:
            return getattr(self, parameter)
        # end if
        raise KeyError("Key {!r} not found".format(parameter))
    # end def

    def __len__(self):
        return len(self.__FIELDS__)
    # end def

    def __iter__(self):
        return iter(self.__FIELDS__)
    # end def

    def __repr__(self):
        return "{name}({args})".format(
            name=self.__class__.__name__,
            args=", ".join("{k}={v!r}".format(k=k, v=self[k]) for k in self.__FIELDS__)
        )
    # end def
# end class

