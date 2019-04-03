from collections.abc import Mapping
# noinspection PyProtectedMember
from typing import Tuple, _VT_co, Iterator


class Kwargs(Mapping):
    __FIELDS__: Tuple[str]

    def __getitem__(self, parameter: str) -> _VT_co:
        """
        Retrieve an object variable
        :param parameter: The current class's parameter to retrieve.
        :raises KeyError: Key not found.
        :return:
        """
        ...

    def __len__(self) -> int:
        ...

    def __iter__(self) -> Iterator[str]:
        """
        The keys of this element.
        """
        ...
