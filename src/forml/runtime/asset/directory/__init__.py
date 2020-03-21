"""Generic assets directory.
"""
import abc
import functools
import logging
import typing
from collections import abc as colabc

from packaging import version

from forml import error  # pylint: disable=unused-import; # noqa: F401
from forml.runtime.asset import persistent

LOGGER = logging.getLogger(__name__)

KeyT = typing.TypeVar('KeyT', str, version.Version, int)
ItemT = typing.TypeVar('ItemT', version.Version, int)


class Level(typing.Generic[KeyT, ItemT], metaclass=abc.ABCMeta):
    """Abstract directory level.
    """
    class Invalid(error.Invalid):
        """Indication of an invalid level.
        """

    class Listing(typing.Generic[ItemT], colabc.Iterable):
        """Helper class representing a registry listing.
        """
        class Empty(error.Missing):
            """Exception indicating empty listing.
            """

        def __init__(self, items: typing.Iterable[ItemT]):
            self._items: typing.Tuple[ItemT] = tuple(sorted(set(items)))

        def __contains__(self, key: ItemT) -> bool:
            return key in self._items

        def __eq__(self, other):
            return isinstance(other, self.__class__) and other._items == self._items

        def __iter__(self):
            return iter(self._items)

        def __str__(self):
            return ', '.join(str(i) for i in self._items)

        @property
        def last(self) -> ItemT:
            """Get the last (most recent) item from the listing.

            Returns: Id of the last item.
            """
            try:
                return self._items[-1]
            except IndexError:
                raise self.Empty('Empty listing')

    def __init__(self, key: typing.Optional[KeyT] = None, parent: typing.Optional['Level'] = None):
        self._key: typing.Optional[KeyT] = key
        self._parent: typing.Optional[Level] = parent

    def __str__(self):
        return f'{self._parent}-{self.key}'

    def __hash__(self):
        return hash(self._parent) ^ hash(self.key)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other._parent == self._parent and other.key == self.key

    @property
    def registry(self) -> 'persistent.Registry':
        """Registry instance.

        Returns: Registry instance.
        """
        return self._parent.registry

    @property
    def key(self) -> KeyT:
        """Either user specified or last lazily listed level key.

        Returns: ID of this level.
        """
        if self._key is None:
            if not self._parent:
                raise ValueError('Parent or key required')
            LOGGER.debug("Determining implicit self key as parent's last listing")
            self._key = self._parent.list().last
        if self._parent and self._key not in self._parent.list():
            raise Level.Invalid(f'Invalid level key {self._key}')
        return self._key

    @abc.abstractmethod
    def list(self) -> 'Level.Listing[ItemT]':
        """Return the listing of this level.

        Returns: Level listing.
        """

    @abc.abstractmethod
    def get(self, key: ItemT) -> 'Level[ItemT, typing.Any]':
        """Get an item from this level.

        Args:
            key: Item key to get.

        Returns: Item as a level instance.
        """


class Cache:
    """Helper for caching registry method calls.
    """
    def __init__(self, method: typing.Callable):
        self._method: str = method.__name__

    def __str__(self):
        return str(self.info)

    @functools.lru_cache()
    def __call__(self, registry: 'persistent.Registry', *args, **kwargs):
        return getattr(registry, self._method)(*args, **kwargs)

    def clear(self) -> None:
        """Clear the cache.
        """
        self.__call__.cache_clear()  # pylint: disable=no-member

    @property
    def info(self) -> functools._CacheInfo:  # pylint: disable=protected-access
        """Return the cache info.

        Returns: Cache info tuple.
        """
        return self.__call__.cache_info()  # pylint: disable=no-value-for-parameter