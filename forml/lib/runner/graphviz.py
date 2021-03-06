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

"""
Runtime that just renders the pipeline DAG visualization.
"""
import logging
import typing

import graphviz as grviz

from forml import conf, runtime
from forml.io import feed as feedmod, sink as sinkmod
from forml.runtime import code
from forml.runtime.asset import access
from forml.runtime.code import instruction

LOGGER = logging.getLogger(__name__)


class Runner(runtime.Runner, alias='graphviz'):
    """Graphviz based runner implementation."""

    FILEPATH = f'{conf.APPNAME}.dot'

    def __init__(
        self,
        assets: typing.Optional[access.Assets] = None,
        feed: typing.Optional[feedmod.Provider] = None,
        sink: typing.Optional[sinkmod.Provider] = None,
        filepath: typing.Optional[str] = None,
        **gvkw: typing.Any,
    ):
        super().__init__(assets, feed, sink)
        self._filepath: str = filepath or self.FILEPATH
        self._gvkw: typing.Mapping[str, typing.Any] = gvkw

    def _run(self, symbols: typing.Sequence[code.Symbol]) -> None:
        dot: grviz.Digraph = grviz.Digraph(**self._gvkw)
        for sym in symbols:
            attrs = dict(shape='ellipse', style='rounded')
            if isinstance(sym.instruction, instruction.Functor):
                attrs.update(shape='box')
            dot.node(repr(id(sym.instruction)), repr(sym.instruction), **attrs)
            for idx, arg in enumerate(sym.arguments):
                dot.edge(repr(id(arg)), repr(id(sym.instruction)), label=repr(idx))
        dot.render(self._filepath, view=True)
