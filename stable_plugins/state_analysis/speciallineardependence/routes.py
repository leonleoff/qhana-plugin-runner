from http import HTTPStatus
from json import dumps
from typing import Mapping, Optional

from celery.canvas import chain
from celery.utils.log import get_task_logger
from flask import Response, abort, redirect
from flask.globals import current_app, request
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
from qhana_plugin_runner.tasks import (
    TASK_STEPS_CHANGED,
    add_step,
    save_task_error,
    save_task_result,
)

from . import CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP, ClassicalStateAnalysisSpeciallineardependence
from .schemas import ClassicalStateAnalysisSpeciallineardependenceParametersSchema
from .tasks import speciallineardependence_task

@CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.route("/")
class PluginsView(MethodView):
    """Plugins collection resource."""

    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.response(HTTPStatus.OK, PluginMetadataSchema())
    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.require_jwt("jwt", optional=True)
    def get(self):
        """Endpoint returning the plugin metadata."""
        plugin = ClassicalStateAnalysisSpeciallineardependence.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)
        return PluginMetadata(
            title=plugin.name,
            description=plugin.description,
            name=plugin.name,
            version=plugin.version,
            type=PluginType.processing,
            entry_point=EntryPoint(
                href=url_for(f"{CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.name}.ProcessView"),
                ui_href=url_for(f"{CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.name}.MicroFrontend"),
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
                        data_type="custom/speciallineardependence-output",
                        content_type=["text/plain"],
                        required=True,
                    )
                ],
            ),
            tags=ClassicalStateAnalysisSpeciallineardependence.instance.tags,
        )


@CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.route("/ui/")
class MicroFrontend(MethodView):
    """Micro frontend for the classical speciallineardependence state analysis plugin."""

    example_inputs = {
    "inputJson": (
        '{\n'
        '    "state": ["0.7071067811865475+0j", "0+0j", "0+0j", "0.7071067811865475+0j"],\n'
        '    "dim_A": 2,\n'
        '    "dim_B": 2,\n'
        '    "tolerance": 1e-10\n'
        '}'
    )
    }


    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.html_response(
        HTTPStatus.OK, description="Micro frontend of the classical speciallineardependence state analysis plugin."
    )
    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.arguments(
        ClassicalStateAnalysisSpeciallineardependenceParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="query",
        required=False,
    )
    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.require_jwt("jwt", optional=True)
    def get(self, errors):
        """Return the micro frontend."""
        return self.render(request.args, errors, False)

    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.html_response(
        HTTPStatus.OK, description="Micro frontend of the classical speciallineardependence state analysis plugin."
    )
    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.arguments(
        ClassicalStateAnalysisSpeciallineardependenceParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="form",
        required=False,
    )
    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.require_jwt("jwt", optional=True)
    def post(self, errors):
        """Return the micro frontend with prerendered inputs."""
        return self.render(request.form, errors, not errors)

    def render(self, data: Mapping, errors: dict, valid: bool):
        plugin = ClassicalStateAnalysisSpeciallineardependence.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)
        schema = ClassicalStateAnalysisSpeciallineardependenceParametersSchema()
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
                process=url_for(f"{CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.name}.ProcessView"),
                help_text="Provide two vectors and a tolerance to check their speciallineardependence.",
                example_values=url_for(
                    f"{CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.name}.MicroFrontend", **self.example_inputs
                ),
            )
    )


@CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.route("/process/")
class ProcessView(MethodView):
    """Start a long running processing task."""

    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.arguments(ClassicalStateAnalysisSpeciallineardependenceParametersSchema(unknown=EXCLUDE), location="form")
    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.response(HTTPStatus.SEE_OTHER)
    @CLASSICAL_ANALYSIS_SPECIALLINEARDEPENDENCE_BLP.require_jwt("jwt", optional=True)
    def post(self, arguments):
        """Start the speciallineardependence analysis task."""
        db_task = ProcessingTask(task_name=speciallineardependence_task.name, parameters=dumps(arguments))
        db_task.save(commit=True)

        # Start the task
        task: chain = speciallineardependence_task.s(db_id=db_task.id) | save_task_result.s(db_id=db_task.id)
        task.link_error(save_task_error.s(db_id=db_task.id))
        task.apply_async()

        db_task.save(commit=True)

        # Redirect to the task view
        return redirect(
            url_for("tasks-api.TaskView", task_id=str(db_task.id)), HTTPStatus.SEE_OTHER
        )
