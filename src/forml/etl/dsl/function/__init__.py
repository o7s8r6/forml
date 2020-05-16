"""
ETL expression language.
"""
import typing

from forml.etl.dsl.schema.series import (  # noqa: F401
    LessThan, LessEqual, GreaterThan, GreaterEqual, Equal, NotEqual, IsNull, NotNull, And, Or, Not)
from forml.etl.dsl.function.conversion import (  # noqa: F401
    Cast)


class Select:
    """ForML ETL select statement.

    This is just a hacked implementation as the the ETL engine concept needs yet to be developed.
    """
    def __init__(self, producer: typing.Callable = None, **params):
        self.producer: typing.Callable = producer
        self.params = params