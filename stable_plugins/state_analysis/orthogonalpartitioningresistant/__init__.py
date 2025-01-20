from typing import Optional

from flask import Flask
from qhana_plugin_runner.api.util import SecurityBlueprint
from qhana_plugin_runner.util.plugins import QHAnaPluginBase, plugin_identifier

_plugin_name = "orthogonalPartitioningResistant_classical"
__version__ = "v0.0.1"
_identifier = plugin_identifier(_plugin_name, __version__)

ORTHOGONAL_PARTITIONING_RESISTANT_BLP = SecurityBlueprint(
    _identifier,
    __name__,
    description="Checks if all vectors form one connected component via orthogonality edges.",
    template_folder="templates",
)


class ClassicalStateAnalysisOrthogonalPartitioningResistant(QHAnaPluginBase):
    """QHAna plugin to see if a set of vectors is all connected by orthogonality edges."""

    name = _plugin_name
    version = __version__
    description = "Checks if all given vectors form a single connected component (via orthogonality edges)."
    tags = ["classical-state-analysis", "orthogonal-partitioning-resistant"]

    def __init__(self, app: Optional[Flask]) -> None:
        super().__init__(app)

    def get_api_blueprint(self):
        return ORTHOGONAL_PARTITIONING_RESISTANT_BLP


try:
    from . import routes
except ImportError:
    pass
