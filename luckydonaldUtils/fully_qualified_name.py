__all__ = (
    'fqn',
)
__author__ = 'luckydonald'

def fqn(obj) -> str:
    """Get the fully qualified name of a class."""
    return f"{obj.__module__}.{obj.__qualname__}"
# end def
