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
    description="A plugin that encodes a list of vectors into a QASM circuit.",
    template_folder="templates",  # Falls du ein eigenes Template-Verzeichnis hast
)


class VectorEncodingPlugin(QHAnaPluginBase):
    name = _plugin_name
    version = __version__
    description = "Encodes a list of complex vectors into QASM code, storing the circuit + metadata."
    tags = ["state-preparation", "demo", "encoding"]

    def __init__(self, app: Optional[Flask]) -> None:
        super().__init__(app)

    def get_api_blueprint(self):
        return ENCODING_BLP


# Wichtig: Routen erst NACH dem Blueprint-Objekt importieren
try:
    from . import routes
except ImportError:
    pass
