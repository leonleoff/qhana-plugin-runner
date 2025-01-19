from http import HTTPStatus
from json import dumps
from typing import Mapping

from celery.canvas import chain
from flask import Response, abort, redirect, request
from flask.helpers import url_for
from flask.templating import render_template
from flask.views import MethodView
from marshmallow import EXCLUDE
from qhana_plugin_runner.api.plugin_schemas import (
    DataMetadata,
    EntryPoint,
    PluginMetadata,
    PluginMetadataSchema,
    PluginType,
)
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.tasks import save_task_error, save_task_result

from . import (
    PAIRWISE_NON_ORTHOGONALITY_BLP,
    ClassicalStateAnalysisPairwiseNonOrthogonality,
)
from .schemas import PairwiseNonOrthogonalityParametersSchema
from .tasks import pairwise_non_orthogonality_task


@PAIRWISE_NON_ORTHOGONALITY_BLP.route("/")
class PluginsView(MethodView):
    """Plugins collection resource for pairwise non-orthogonality."""

    @PAIRWISE_NON_ORTHOGONALITY_BLP.response(HTTPStatus.OK, PluginMetadataSchema())
    def get(self):
        """Return the plugin metadata."""
        plugin = ClassicalStateAnalysisPairwiseNonOrthogonality.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        return PluginMetadata(
            title=plugin.name,
            description=plugin.description,
            name=plugin.name,
            version=plugin.version,
            type=PluginType.processing,
            entry_point=EntryPoint(
                href=url_for(f"{PAIRWISE_NON_ORTHOGONALITY_BLP.name}.ProcessView"),
                ui_href=url_for(f"{PAIRWISE_NON_ORTHOGONALITY_BLP.name}.MicroFrontend"),
                plugin_dependencies=[],
                data_input=[
                    DataMetadata(
                        data_type="application/json",
                        content_type=["application/json"],
                        required=True,
                    )
                ],
                data_output=[
                    DataMetadata(
                        data_type="custom/pairwise-non-orthogonality-output",
                        content_type=["text/plain"],
                        required=True,
                    )
                ],
            ),
            tags=plugin.tags,
        )


@PAIRWISE_NON_ORTHOGONALITY_BLP.route("/ui/")
class MicroFrontend(MethodView):
    """Micro frontend for pairwise non-orthogonality."""

    # Beispiel-Eingaben
    vectors_example = [
        [[1.0, 0.0], [0.0, 0.0]],
        [[0.0, 0.0], [1.0, 0.0]],
        [[1.0, 0.0], [1.0, 0.0]],
    ]
    example_inputs = {
        "vectors": f"{vectors_example}",
        "tolerance": "1e-10",
    }

    @PAIRWISE_NON_ORTHOGONALITY_BLP.html_response(
        HTTPStatus.OK,
        description="Micro frontend of the pairwise non-orthogonality plugin.",
    )
    @PAIRWISE_NON_ORTHOGONALITY_BLP.arguments(
        PairwiseNonOrthogonalityParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="query",
        required=False,
    )
    def get(self, errors):
        """Return the micro frontend (GET)."""
        return self.render(request.args, errors, valid=False)

    @PAIRWISE_NON_ORTHOGONALITY_BLP.html_response(
        HTTPStatus.OK,
        description="Micro frontend of the pairwise non-orthogonality plugin.",
    )
    @PAIRWISE_NON_ORTHOGONALITY_BLP.arguments(
        PairwiseNonOrthogonalityParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="form",
        required=False,
    )
    def post(self, errors):
        """Return the micro frontend with prerendered inputs (POST)."""
        return self.render(request.form, errors, valid=(not errors))

    def render(self, data: Mapping, errors: dict, valid: bool):
        plugin = ClassicalStateAnalysisPairwiseNonOrthogonality.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        schema = PairwiseNonOrthogonalityParametersSchema()
        result = None
        task_id = data.get("task_id")
        if task_id:
            task = ProcessingTask.get_by_id(task_id)
            if task:
                result = task.result

        return Response(
            render_template(
                "simple_template.html",
                name=plugin.name,
                version=plugin.version,
                schema=schema,
                valid=valid,
                values=data,
                errors=errors,
                result=result,
                process=url_for(f"{PAIRWISE_NON_ORTHOGONALITY_BLP.name}.ProcessView"),
                help_text="Check if all vectors are pairwise orthogonal. Returns True or False.",
                example_values=url_for(
                    f"{PAIRWISE_NON_ORTHOGONALITY_BLP.name}.MicroFrontend",
                    **self.example_inputs,
                ),
            )
        )


@PAIRWISE_NON_ORTHOGONALITY_BLP.route("/process/")
class ProcessView(MethodView):
    """Start a long running processing task."""

    @PAIRWISE_NON_ORTHOGONALITY_BLP.arguments(
        PairwiseNonOrthogonalityParametersSchema(unknown=EXCLUDE),
        location="form",
    )
    @PAIRWISE_NON_ORTHOGONALITY_BLP.response(HTTPStatus.SEE_OTHER)
    def post(self, arguments):
        """Start the pairwise-non-orthogonality check task."""
        from qhana_plugin_runner.db.models.tasks import ProcessingTask

        db_task = ProcessingTask(
            task_name=pairwise_non_orthogonality_task.name, parameters=dumps(arguments)
        )
        db_task.save(commit=True)

        # Verkette Tasks (falls benötigt), hier aber nur eine
        task_chain = pairwise_non_orthogonality_task.s(
            db_id=db_task.id
        ) | save_task_result.s(db_id=db_task.id)
        task_chain.link_error(save_task_error.s(db_id=db_task.id))
        task_chain.apply_async()

        db_task.save(commit=True)

        return redirect(
            url_for("tasks-api.TaskView", task_id=str(db_task.id)),
            code=HTTPStatus.SEE_OTHER,
        )
