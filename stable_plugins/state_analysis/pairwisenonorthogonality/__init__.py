from typing import Optional

from flask import Flask
from qhana_plugin_runner.api.util import SecurityBlueprint
from qhana_plugin_runner.util.plugins import QHAnaPluginBase, plugin_identifier

_plugin_name = "pairwiseOrthogonality_classical"
__version__ = "v0.0.1"
_identifier = plugin_identifier(_plugin_name, __version__)

PAIRWISE_ORTHOGONALITY_BLP = SecurityBlueprint(
    _identifier,
    __name__,
    description="Pairwise Orthogonality plugin API.",
    template_folder="templates",
)


class ClassicalStateAnalysisPairwiseOrthogonality(QHAnaPluginBase):
    name = _plugin_name
    version = __version__
    description = "Checks whether all vectors in a set are pairwise orthogonal or not."
    tags = ["classical-state-analysis", "pairwise-orthogonality"]

    def __init__(self, app: Optional[Flask]) -> None:
        super().__init__(app)

    def get_api_blueprint(self):
        return PAIRWISE_ORTHOGONALITY_BLP


try:
    # Routen erst importieren, nachdem das Blueprint definiert wurde
    from . import routes
except ImportError:
    pass
