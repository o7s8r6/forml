"""
Stdlib actors.
"""

import inspect
import typing

from forml.flow import task


class Wrapping:
    """Base class for actor wrapping.
    """
    def __init__(self, actor: typing.Type, mapping: typing.Mapping[str, str]):
        self._actor: typing.Any = actor
        self._mapping: typing.Mapping[str, str] = mapping

    def is_stateful(self) -> bool:
        """Emulation of native actor is_stateful class method.

        Returns: True if the wrapped actor is stateful (has a train method).
        """
        return hasattr(self._actor, self._mapping[task.Actor.train.__name__])


class Wrapped(Wrapping):
    """Decorator wrapper.
    """
    class Actor(Wrapping, task.Actor):  # pylint: disable=abstract-method
        """Wrapper around user class implementing the Actor interface.
        """
        def __new__(cls, actor: typing.Any, mapping: typing.Mapping[str, str]):  # pylint: disable=unused-argument
            cls.__abstractmethods__ = frozenset()
            return super().__new__(cls)

        def __init__(self, actor: typing.Any, mapping: typing.Mapping[str, str]):
            super().__init__(actor, mapping)

        def __getnewargs__(self):
            return self._actor, self._mapping

        def __getattribute__(self, item):
            if item.startswith('_') or item not in self._mapping and not hasattr(self._actor, item):
                return super().__getattribute__(item)
            return getattr(self._actor, self._mapping.get(item, item))

    def __init__(self, actor: typing.Type, mapping: typing.Mapping[str, str]):
        assert not issubclass(actor, task.Actor), 'Wrapping a true actor'
        super().__init__(actor, mapping)

    def __str__(self):
        return str(self._actor.__name__)

    def __call__(self, *args, **kwargs) -> task.Actor:
        return self.Actor(self._actor(*args, **kwargs), self._mapping)  # pylint: disable=abstract-class-instantiated

    def __hash__(self):
        return hash(self._actor) ^ hash(tuple(sorted(self._mapping.items())))

    def __eq__(self, other: typing.Any):
        # pylint: disable=protected-access
        return isinstance(other, self.__class__) and self._actor == other._actor and self._mapping == other._mapping

    def spec(self, **params) -> task.Spec:
        """Shortcut for creating a spec of this actor.

        Args:
            **params: Params to be used for the spec.

        Returns: Actor spec instance.
        """
        return task.Spec(self, **params)

    @staticmethod
    def actor(cls: typing.Optional[typing.Type] = None, **mapping: str):  # pylint: disable=bad-staticmethod-argument
        """Decorator for turning an user class to a valid actor. This can be used either as parameterless decorator or
        optionally with mapping of Actor methods to decorated user class implementation.

        Args:
            cls: Decorated class.
            apply: Name of user class method implementing the actor apply.
            train: Name of user class method implementing the actor train.
            get_params: Name of user class method implementing the actor get_params.
            set_params: Name of user class method implementing the actor set_params.

        Returns: Actor class.
        """
        assert all(isinstance(a, str) for a in mapping.values()), 'Invalid mapping'

        for method in (task.Actor.apply, task.Actor.train, task.Actor.get_params, task.Actor.set_params):
            mapping.setdefault(method.__name__, method.__name__)

        def decorator(cls):
            """Decorating function.
            """
            assert cls and inspect.isclass(cls), f'Invalid actor class {cls}'
            if isinstance(cls, task.Actor):
                return cls
            for target in {t for s, t in mapping.items() if s != task.Actor.train.__name__}:
                assert callable(getattr(cls, target, None)), f'Wrapped actor missing required {target} implementation'
            return Wrapped(cls, mapping)

        if cls:
            decorator = decorator(cls)
        return decorator