"""
Runtime process layer.
"""
import abc
import typing

from forml import provider, etl, error
from forml.conf import provider as provcfg
from forml.etl.dsl.schema import kind
from forml.flow import pipeline
from forml.runtime import code
from forml.runtime.asset import access
from forml.runtime.code import compiler


class Runner(provider.Interface, default=provcfg.Runner.default):
    """Abstract base runtime class to be extended by particular runtime implementations.
    """
    def __init__(self, assets: typing.Optional[access.Assets] = None, feed: typing.Optional['etl.Feed'] = None):
        self._assets: access.Assets = assets or access.Assets()
        self._feed: etl.Feed = feed or etl.Feed()

    def train(self, lower: typing.Optional['kind.Native'] = None,
              upper: typing.Optional['kind.Native'] = None) -> typing.Any:
        """Run the training code.

        Args:
            lower: Ordinal value as the lower bound for the ETL cycle.
            upper:  Ordinal value as the upper bound for the ETL cycle.
        """
        composition = self._build(lower or self._assets.tag.training.ordinal, upper,
                                  self._assets.project.pipeline)
        return self._exec(composition.train,
                          self._assets.state(composition.shared, self._assets.tag.training.trigger()))

    def apply(self, lower: typing.Optional['kind.Native'] = None,
              upper: typing.Optional['kind.Native'] = None) -> typing.Any:
        """Run the applying code.

        Args:
            lower: Ordinal value as the lower bound for the ETL cycle.
            upper:  Ordinal value as the upper bound for the ETL cycle.

        Returns: Applying code.
        """
        composition = self._build(lower, upper, self._assets.project.pipeline)
        return self._exec(composition.apply, self._assets.state(composition.shared))

    def cvscore(self, lower: typing.Optional['kind.Native'] = None,
                upper: typing.Optional['kind.Native'] = None) -> typing.Any:
        """Run the crossvalidating evaluation.

        Args:
            lower: Ordinal value as the lower bound for the ETL cycle.
            upper:  Ordinal value as the upper bound for the ETL cycle.

        Returns: Crossvalidate evaluation score.
        """
        return self._exec(self._evaluation(lower, upper).train)

    def _evaluation(self, lower: typing.Optional['kind.Native'] = None,
                    upper: typing.Optional['kind.Native'] = None) -> pipeline.Segment:
        """Return the evaluation pipeline.

        Args:
            lower: Ordinal value as the lower bound for the ETL cycle.
            upper:  Ordinal value as the upper bound for the ETL cycle.

        Returns: Evaluation pipeline.
        """
        if not self._assets.project.evaluation:
            raise error.Invalid('Project not evaluable')
        return self._build(lower, upper, self._assets.project.pipeline >> self._assets.project.evaluation)

    def _build(self, lower: typing.Optional['kind.Native'], upper: typing.Optional['kind.Native'],
               *blocks: pipeline.Segment) -> pipeline.Composition:
        """Assemble the chain of blocks with the mandatory ETL cycle.

        Args:
            lower: Ordinal value as the lower bound for the ETL cycle.
            upper:  Ordinal value as the upper bound for the ETL cycle.
            *blocks: Additional block to assemble.

        Returns: Assembled flow pipeline.
        """
        return pipeline.Composition(self._feed.load(self._assets.project.source, lower, upper),
                                    *(b.expand() for b in blocks))

    def _exec(self, path: pipeline.Segment, assets: typing.Optional[access.State] = None) -> typing.Any:
        """Execute the given path and assets.

        Args:
            path: Pipeline path.
            assets: Persistent assets to be used.

        Returns: Optional return value.
        """
        return self._run(compiler.generate(path, assets))

    @abc.abstractmethod
    def _run(self, symbols: typing.Sequence[code.Symbol]) -> typing.Any:
        """Actual run action to be implemented according to the specific runtime.

        Args:
            symbols: task graph to be executed.

        Returns: Optional pipeline return value.
        """
