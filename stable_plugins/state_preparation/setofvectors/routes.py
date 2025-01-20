from http import HTTPStatus
from json import dumps
from typing import Mapping, Optional

from celery.canvas import chain
from flask import Response, abort, redirect, render_template, request
from flask.helpers import url_for
from flask.views import MethodView
from marshmallow import EXCLUDE
from qhana_plugin_runner.api.plugin_schemas import (
    DataMetadata,
    EntryPoint,
    OutputDataMetadata,
    PluginMetadata,
    PluginMetadataSchema,
    PluginType,
)
from qhana_plugin_runner.api.util import SecurityBlueprint
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.tasks import save_task_error, save_task_result

from . import ENCODING_BLP, VectorEncodingPlugin
from .schemas import VectorsToQasmParametersSchema
from .tasks import vector_encoding_task


@ENCODING_BLP.route("/")
class PluginView(MethodView):
    """Plugins collection resource for the vector encoding plugin."""

    @ENCODING_BLP.response(HTTPStatus.OK, PluginMetadataSchema())
    def get(self):
        """Return the plugin metadata."""
        plugin = VectorEncodingPlugin.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        return PluginMetadata(
            title=plugin.name,
            description=plugin.description,
            name=plugin.name,
            version=plugin.version,
            type=PluginType.processing,
            entry_point=EntryPoint(
                href=url_for(f"{ENCODING_BLP.name}.ProcessView"),
                ui_href=url_for(f"{ENCODING_BLP.name}.MicroFrontend"),
                plugin_dependencies=[],
                data_input=[
                    DataMetadata(
                        data_type="application/json",
                        content_type=["application/json"],
                        required=True,
                    )
                ],
                data_output=[
                    OutputDataMetadata(
                        data_type="executable/circuit",
                        content_type=["text/x-qasm"],
                        required=True,
                        name="encoded_circuit.qasm",
                    ),
                    OutputDataMetadata(
                        data_type="application/json",
                        content_type=["application/json"],
                        required=True,
                        name="circuit_borders.json",
                    ),
                ],
            ),
            tags=plugin.tags,
        )


@ENCODING_BLP.route("/ui/")
class MicroFrontend(MethodView):
    """Simple micro-frontend for the vector encoding plugin."""

    example_vectors = [
        [[1.0, 0.0], [0.0, 0.0]],
        [[0.0, 0.0], [0.0, 1.0]],
    ]

    example_inputs = {
        "vectors": f"{example_vectors}",
    }

    @ENCODING_BLP.html_response(HTTPStatus.OK, description="Micro frontend (GET).")
    @ENCODING_BLP.arguments(
        VectorsToQasmParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="query",
        required=False,
    )
    def get(self, errors):
        return self.render(request.args, errors, valid=False)

    @ENCODING_BLP.html_response(HTTPStatus.OK, description="Micro frontend (POST).")
    @ENCODING_BLP.arguments(
        VectorsToQasmParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="form",
        required=False,
    )
    def post(self, errors):
        return self.render(request.form, errors, valid=(not errors))

    def render(self, data: Mapping, errors: dict, valid: bool):
        plugin = VectorEncodingPlugin.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        schema = VectorsToQasmParametersSchema()
        return Response(
            render_template(
                "simple_template.html",
                name=plugin.name,
                version=plugin.version,
                schema=schema,
                valid=valid,
                values=data,
                errors=errors,
                process=url_for(f"{ENCODING_BLP.name}.ProcessView"),
                help_text="Provide two vectors and a tolerance to check their lineardependence.",
                example_values=url_for(
                    f"{ENCODING_BLP.name}.MicroFrontend",
                    **self.example_inputs,
                ),
            )
        )


@ENCODING_BLP.route("/process/")
class ProcessView(MethodView):
    """Start a long running processing task."""

    @ENCODING_BLP.arguments(
        VectorsToQasmParametersSchema(unknown=EXCLUDE),
        location="form",
    )
    @ENCODING_BLP.response(HTTPStatus.SEE_OTHER)
    @ENCODING_BLP.require_jwt("jwt", optional=True)
    def post(self, arguments):
        """Start the vector-encoding task."""
        db_task = ProcessingTask(
            task_name=vector_encoding_task.name, parameters=dumps(arguments)
        )
        db_task.save(commit=True)

        # Start the task
        task: chain = vector_encoding_task.s(db_id=db_task.id) | save_task_result.s(
            db_id=db_task.id
        )
        task.link_error(save_task_error.s(db_id=db_task.id))
        task.apply_async()

        db_task.save(commit=True)

        # Redirect to the task view
        return redirect(
            url_for("tasks-api.TaskView", task_id=str(db_task.id)), HTTPStatus.SEE_OTHER
        )
