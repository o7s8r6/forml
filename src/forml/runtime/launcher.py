# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Special runtime launchers.
"""
import logging
import multiprocessing
import queue as quemod
import typing

from forml import runtime
from forml.conf.parsed import provider as provcfg
from forml.io import feed as feedmod, sink as sinkmod  # pylint: disable=unused-import
from forml.io import payload
from forml.io.dsl.struct import kind
from forml.lib.registry import virtual
from forml.project import distribution
from forml.runtime.asset import persistent
from forml.runtime.asset.directory import root

LOGGER = logging.getLogger(__name__)


class Virtual:
    """Launcher that allows executing provided distribution package using a special pipeline sink to capture and return
    any output generated by given mode.
    """
    class Builder:
        """Wrapper for selected launcher parameters.
        """
        class Handler:
            """Actual callable as a proxy for the specific launcher callback.
            """
            class Sink(sinkmod.Provider):
                """Special sink to forward the output to a multiprocessing.Queue.
                """
                class Writer(sinkmod.Provider.Writer):
                    """Sink writer.
                    """
                    @classmethod
                    def write(cls, data: payload.Native, queue: multiprocessing.Queue) -> None:
                        queue.put(data, block=False)

            def __init__(self, builder: 'Virtual.Builder', mode: property):
                self._builder: Virtual.Builder = builder
                self._mode: property = mode

            def __call__(self, lower: typing.Optional[kind.Native] = None,
                         upper: typing.Optional[kind.Native] = None) -> typing.Any:
                with multiprocessing.Manager() as manager:
                    output = manager.Queue()
                    self._mode.fget(self._builder(self.Sink(queue=output)))(lower, upper)
                    try:
                        return output.get(block=False)
                    except quemod.Empty:
                        LOGGER.warning('Runner finished but sink queue empty')
                        return None

        train = property(lambda self: Virtual.Builder.Handler(self, runtime.Platform.Launcher.train))
        apply = property(lambda self: Virtual.Builder.Handler(self, runtime.Platform.Launcher.apply))
        eval = property(lambda self: Virtual.Builder.Handler(self, runtime.Platform.Launcher.eval))
        tune = property(lambda self: Virtual.Builder.Handler(self, runtime.Platform.Launcher.tune))

        def __init__(self, runner: typing.Optional[provcfg.Runner], registry: persistent.Registry,
                     feeds: typing.Optional[typing.Iterable[typing.Union[provcfg.Feed, str, 'feedmod.Provider']]],
                     project: str):
            self._runner: typing.Optional[provcfg.Runner] = runner
            self._registry: persistent.Registry = registry
            self._feeds: typing.Optional[typing.Iterable[typing.Union[provcfg.Feed, str, 'feedmod.Provider']]] = feeds
            self._project: str = project

        def __call__(self, sink: sinkmod.Provider) -> runtime.Platform.Launcher:
            return runtime.Platform(self._runner, self._registry, self._feeds, sink).launcher(self._project)

    def __init__(self, package: distribution.Package):
        self._project: str = package.manifest.name
        self._registry: persistent.Registry = virtual.Registry()
        root.Level(self._registry).get(self._project).put(package)

    def __call__(self, runner: typing.Optional[provcfg.Runner] = None, feeds: typing.Optional[
            typing.Iterable[typing.Union[provcfg.Feed, str, 'feedmod.Provider']]] = None) -> 'Virtual.Builder':
        return self.Builder(runner, self._registry, feeds, self._project)

    def __getitem__(self, runner: str) -> 'Virtual.Builder':
        """Convenient shortcut for selecting a specific runner using the `launcher[name]` syntax.

        Args:
            runner: Runner alias/qualname to use.

        Returns: Launcher builder.
        """
        return self(provcfg.Runner.resolve(runner))

    def __getattr__(self, mode: str) -> 'Virtual.Builder.Mode.Handler':
        """Convenient shortcut for accessing the particular launcher mode using the `launcher.train()` syntax.

        Args:
            mode: Launcher mode to execute.

        Returns: Callable launcher handler.
        """
        return getattr(self(), mode)
