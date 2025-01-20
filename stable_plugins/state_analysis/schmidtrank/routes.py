from http import HTTPStatus
from json import dumps
from typing import Mapping

from celery.canvas import chain
from flask import Response, abort, redirect, render_template, request
from flask.helpers import url_for
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

from . import CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP, ClassicalStateAnalysisSchmidtrank
from .schemas import ClassicalStateAnalysisSchmidtrankParametersSchema
from .tasks import schmidtrank_task


@CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.route("/")
class PluginsView(MethodView):
    """Returns plugin metadata for Schmidt-rank analysis."""

    @CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.response(HTTPStatus.OK, PluginMetadataSchema())
    def get(self):
        plugin = ClassicalStateAnalysisSchmidtrank.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        return PluginMetadata(
            title=plugin.name,
            description=plugin.description,
            name=plugin.name,
            version=plugin.version,
            type=PluginType.processing,
            entry_point=EntryPoint(
                href=url_for(f"{CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.name}.ProcessView"),
                ui_href=url_for(
                    f"{CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.name}.MicroFrontend"
                ),
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
                        data_type="custom/schmidtrank-output",
                        content_type=["text/plain"],
                        required=True,
                    )
                ],
            ),
            tags=plugin.tags,
        )


@CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.route("/ui/")
class MicroFrontend(MethodView):
    """
    A UI for the Schmidt rank plugin (single vector, or circuit-based).
    """

    vector = [
        [0.7071067811865475, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.7071067811865475, 0.0],
    ]
    example_inputs = {
        "vector": f"{vector}",
        "dimA": 2,
        "dimB": 2,
        "tolerance": "1e-10",
    }

    @CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.html_response(
        HTTPStatus.OK, description="Schmidtrank plugin UI (GET)."
    )
    @CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.arguments(
        ClassicalStateAnalysisSchmidtrankParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="query",
        required=False,
    )
    def get(self, errors):
        return self.render(request.args, errors, valid=False)

    @CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.html_response(
        HTTPStatus.OK, description="Schmidtrank plugin UI (POST)."
    )
    @CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.arguments(
        ClassicalStateAnalysisSchmidtrankParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="form",
        required=False,
    )
    def post(self, errors):
        return self.render(request.form, errors, valid=(not errors))

    def render(self, data: Mapping, errors: dict, valid: bool):
        plugin = ClassicalStateAnalysisSchmidtrank.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        schema = ClassicalStateAnalysisSchmidtrankParametersSchema()
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
                process=url_for(f"{CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.name}.ProcessView"),
                help_text="Provide one vector with dimA, dimB or a circuit descriptor with dimA, dimB. The plugin computes the Schmidt rank.",
                example_values=url_for(
                    f"{CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.name}.MicroFrontend",
                    **self.example_inputs,
                ),
            )
        )


@CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.route("/process/")
class ProcessView(MethodView):
    """Starts the Schmidt-rank analysis task."""

    @CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.arguments(
        ClassicalStateAnalysisSchmidtrankParametersSchema(unknown=EXCLUDE),
        location="form",
    )
    @CLASSICAL_ANALYSIS_SCHMIDTRANK_BLP.response(HTTPStatus.SEE_OTHER)
    def post(self, arguments):
        db_task = ProcessingTask(
            task_name=schmidtrank_task.name, parameters=dumps(arguments)
        )
        db_task.save(commit=True)

        # Start the task
        task: chain = schmidtrank_task.s(db_id=db_task.id) | save_task_result.s(
            db_id=db_task.id
        )
        task.link_error(save_task_error.s(db_id=db_task.id))
        task.apply_async()

        db_task.save(commit=True)

        # Redirect to the task view
        return redirect(
            url_for("tasks-api.TaskView", task_id=str(db_task.id)), HTTPStatus.SEE_OTHER
        )
