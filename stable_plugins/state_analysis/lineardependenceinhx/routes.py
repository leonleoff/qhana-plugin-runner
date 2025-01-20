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

from . import (
    CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP,
    ClassicalStateAnalysisLineardependenceInHX,
)
from .schemas import ClassicalStateAnalysisLineardependenceInHXParametersSchema
from .tasks import lineardependenceInHX_task


@CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.route("/")
class PluginsView(MethodView):
    """Returns plugin metadata for lineardependenceInHX."""

    @CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.response(
        HTTPStatus.OK, PluginMetadataSchema()
    )
    @CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.require_jwt("jwt", optional=True)
    def get(self):
        plugin = ClassicalStateAnalysisLineardependenceInHX.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        return PluginMetadata(
            title=plugin.name,
            description=plugin.description,
            name=plugin.name,
            version=plugin.version,
            type=PluginType.processing,
            entry_point=EntryPoint(
                href=url_for(
                    f"{CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.name}.ProcessView"
                ),
                ui_href=url_for(
                    f"{CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.name}.MicroFrontend"
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
                        data_type="custom/lineardependenceInHX-output",
                        content_type=["text/plain"],
                        required=True,
                    )
                ],
            ),
            tags=plugin.tags,
        )


@CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.route("/ui/")
class MicroFrontend(MethodView):
    """
    A basic UI for the lineardependenceInHX plugin, with vectors or circuit input.
    """

    example_vectors = [
        [
            [0.7071067811865475, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
            [0.7071067811865475, 0.0],
        ],
        [
            [1.0, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
            [0.0, 0.0],
        ],
    ]
    example_inputs = {
        "vectors": f"{example_vectors}",
        "dimA": 2,
        "dimB": 2,
        "singularValueTolerance": "1e-10",
        "linearDependenceTolerance": "1e-10",
    }

    @CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.html_response(
        HTTPStatus.OK,
        description="lineardependenceInHX plugin UI (GET).",
    )
    @CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.arguments(
        ClassicalStateAnalysisLineardependenceInHXParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="query",
        required=False,
    )
    @CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.require_jwt("jwt", optional=True)
    def get(self, errors):
        return self.render(request.args, errors, valid=False)

    @CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.html_response(
        HTTPStatus.OK,
        description="lineardependenceInHX plugin UI (POST).",
    )
    @CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.arguments(
        ClassicalStateAnalysisLineardependenceInHXParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="form",
        required=False,
    )
    @CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.require_jwt("jwt", optional=True)
    def post(self, errors):
        return self.render(request.form, errors, valid=(not errors))

    def render(self, data: Mapping, errors: dict, valid: bool):
        plugin = ClassicalStateAnalysisLineardependenceInHX.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        schema = ClassicalStateAnalysisLineardependenceInHXParametersSchema()
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
                process=url_for(
                    f"{CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.name}.ProcessView"
                ),
                help_text="Enter vectors with dimA/dimB or provide a circuit descriptor. Checks linear dependence in Hx.",
                example_values=url_for(
                    f"{CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.name}.MicroFrontend",
                    **self.example_inputs,
                ),
            )
        )


@CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.route("/process/")
class ProcessView(MethodView):
    """
    Starts the lineardependenceInHX analysis.
    """

    @CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.arguments(
        ClassicalStateAnalysisLineardependenceInHXParametersSchema(unknown=EXCLUDE),
        location="form",
    )
    @CLASSICAL_ANALYSIS_LINEARDEPENDENCEINHX_BLP.response(HTTPStatus.SEE_OTHER)
    def post(self, arguments):
        db_task = ProcessingTask(
            task_name=lineardependenceInHX_task.name,
            parameters=dumps(arguments),
        )
        db_task.save(commit=True)

        # Start the task
        task: chain = lineardependenceInHX_task.s(db_id=db_task.id) | save_task_result.s(
            db_id=db_task.id
        )
        task.link_error(save_task_error.s(db_id=db_task.id))
        task.apply_async()

        db_task.save(commit=True)

        return redirect(
            url_for("tasks-api.TaskView", task_id=str(db_task.id)), HTTPStatus.SEE_OTHER
        )
