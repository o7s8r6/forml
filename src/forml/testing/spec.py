"""
Testing specification elements.
"""
import abc
import collections
import enum
import functools
import types
import typing


class Scenario(collections.namedtuple('Scenario', 'params, input, output, exception')):
    """Test case specification.
    """
    @enum.unique
    class Outcome(enum.Enum):
        """Possible outcome type.
        """
        INIT_RAISES = 'init-raises'
        PLAINAPPLY_RAISES = 'plainapply-raises'
        PLAINAPPLY_RETURNS = 'plainapply-returns'
        STATETRAIN_RAISES = 'statetrain-raises'
        STATETRAIN_RETURNS = 'statetrain-returns'
        STATEAPPLY_RAISES = 'stateapply-raises'
        STATEAPPLY_RETURNS = 'stateapply-returns'

        @property
        def raises(self) -> bool:
            """True if this outcome is one of the raises.
            """
            return self in {self.INIT_RAISES, self.PLAINAPPLY_RAISES, self.STATEAPPLY_RAISES}

    class Digest(collections.namedtuple('Digest', 'trained, applied, raised')):
        """Scenario combination fingerprint.
        """

    OUTCOME = {
        Digest(False, False, True): Outcome.INIT_RAISES,
        Digest(False, True, True): Outcome.PLAINAPPLY_RAISES,
        Digest(False, True, False): Outcome.PLAINAPPLY_RETURNS,
        Digest(True, False, True): Outcome.STATETRAIN_RAISES,
        Digest(True, False, False): Outcome.STATETRAIN_RETURNS,
        Digest(True, True, True): Outcome.STATEAPPLY_RAISES,
        Digest(True, True, False): Outcome.STATEAPPLY_RETURNS,
    }

    class Params(collections.namedtuple('Params', 'args, kwargs')):
        """Operator hyper-parameters.
        """
        def __new__(cls, *args: typing.Any, **kwargs: typing.Any):
            return super().__new__(cls, args, types.MappingProxyType(kwargs))

        def __hash__(self):
            return hash(self.args) ^ hash(tuple(sorted(self.kwargs.items())))

    class IO(metaclass=abc.ABCMeta):
        """Input/output base class.
        """
        @property
        @abc.abstractmethod
        def apply(self) -> typing.Any:
            """Apply dataset.

            Returns: The apply dataset.
            """

        def __bool__(self):
            return self.applied or self.trained

        @property
        def applied(self) -> bool:
            """Test this is a (to-be) applied in/output.
            """
            return self.apply is not None

        @property
        @abc.abstractmethod
        def trained(self) -> bool:
            """Test this is a to-be trained in/output.
            """

    class Input(collections.namedtuple('Input', 'apply, train, label'), IO):
        """Input data type.
        """
        def __new__(cls, apply: typing.Any = None, train: typing.Any = None, label: typing.Any = None):
            return super().__new__(cls, apply, train, label)

        @property
        def trained(self) -> bool:
            """Test this is a to-be trained input.
            """
            return self.train is not None or self.label is not None

    class Output(collections.namedtuple('Output', 'apply, train, matcher'), IO):
        """Output data type.
        """
        def __new__(cls, apply: typing.Any = None, train: typing.Any = None,
                    matcher: typing.Optional[typing.Callable[[typing.Any, typing.Any], bool]] = None):
            if apply is not None and train is not None:
                raise ValueError('Output apply/train collision')
            return super().__new__(cls, apply, train, matcher)

        @property
        def trained(self) -> bool:
            """Test this is a trained output.
            """
            return self.train is not None

        @property
        def value(self) -> typing.Any:
            """Return the trained or applied exclusive value.

            Returns: Trained or applied value.
            """
            return self.train if self.trained else self.apply

    class Exception(collections.namedtuple('Exception', 'kind, message')):
        """Exception type.
        """
        def __new__(cls, kind: typing.Type[Exception], message: typing.Optional[str] = None):
            if not issubclass(kind, Exception):
                raise ValueError('Invalid exception type')
            return super().__new__(cls, kind, message)

    def __new__(cls, params: 'Scenario.Params',
                input: typing.Optional['Scenario.Input'] = None,  # pylint: disable=redefined-builtin
                output: typing.Optional['Scenario.Output'] = None,
                exception: typing.Optional[typing.Type[Exception]] = None):
        if not output:
            output = cls.Output()
        if not input:
            input = cls.Input()
            if output:
                raise ValueError('Output without input')
            if not exception:
                raise ValueError('Unknown outcome')
        return super().__new__(cls, params, input, output, exception)

    def __hash__(self):
        return hash(self.params) ^ hash(self.input.trained) ^ hash(self.input.applied) ^ hash(self.exception)

    @property
    @functools.lru_cache()
    def outcome(self) -> 'Scenario.Outcome':
        """The outcome type of this scenario.

        Returns: Outcome type.
        """
        return self.OUTCOME[self.Digest(self.input.trained, self.input.applied, self.exception is not None)]


class Raisable:
    """Base outcome type allowing a raising assertion.
    """
    def __init__(self, params: 'Scenario.Params',
                 input: typing.Optional['Scenario.IO'] = None):  # pylint: disable=redefined-builtin
        self._params: Scenario.Params = params
        self._input: Scenario.Input = input or Scenario.Input()

    def raises(self, kind: typing.Type[Exception], message: typing.Optional[str] = None) -> Scenario:
        """Assertion on expected exception.
        """
        return Scenario(self._params, self._input, exception=Scenario.Exception(kind, message))


class Applied(Raisable):
    """Outcome with a apply input dataset defined.
    """
    def returns(self, output: typing.Any,
                matcher: typing.Optional[typing.Callable[[typing.Any, typing.Any], bool]] = None) -> Scenario:
        """Assertion on expected return value.
        """
        return Scenario(self._params, self._input, Scenario.Output(apply=output, matcher=matcher))


class Appliable(Raisable):
    """Outcome type allowing to define an apply input dataset.
    """
    def apply(self, features: typing.Any) -> Applied:
        """Apply input dataset definition.
        """
        return Applied(self._params, self._input._replace(apply=features))


class Trained(Appliable):
    """Outcome with a train input dataset defined.
    """
    def returns(self, output: typing.Any,
                matcher: typing.Optional[typing.Callable[[typing.Any, typing.Any], bool]] = None) -> Scenario:
        """Assertion on expected return value.
        """
        return Scenario(self._params, self._input, Scenario.Output(train=output, matcher=matcher))
