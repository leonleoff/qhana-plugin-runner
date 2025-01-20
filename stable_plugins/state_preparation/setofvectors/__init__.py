# Copyright 2022 QHAna plugin runner contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Optional

from flask import Flask
from qhana_plugin_runner.api.util import SecurityBlueprint
from qhana_plugin_runner.util.plugins import QHAnaPluginBase, plugin_identifier

_plugin_name = "vectorEncoding_classical"
__version__ = "v0.0.1"
_identifier = plugin_identifier(_plugin_name, __version__)

ENCODING_BLP = SecurityBlueprint(
    _identifier,
    __name__,
    description="A plugin that encodes a list of vectors into a QASM circuit (QuantumCircuitDescriptor).",
    template_folder="templates",
)


class VectorEncodingPlugin(QHAnaPluginBase):
    """QHAna plugin that encodes one or more complex vectors into QASM."""

    name = _plugin_name
    version = __version__
    description = (
        "Encodes a list of complex vectors into QASM code, storing circuit + metadata."
    )
    tags = ["state-preparation", "demo", "encoding"]

    def __init__(self, app: Optional[Flask]) -> None:
        super().__init__(app)

    def get_api_blueprint(self):
        return ENCODING_BLP


try:
    from . import routes
except ImportError:
    pass
