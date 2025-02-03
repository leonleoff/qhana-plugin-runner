from http import HTTPStatus
from json import dumps
from typing import Mapping

from celery.canvas import chain
from flask import Response, abort, redirect, render_template, request, url_for
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
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.tasks import save_task_error, save_task_result

from . import FILES_BLP, FilesMakerPlugin
from .schemas import TextsToFilesParametersSchema
from .tasks import store_texts_task


@FILES_BLP.route("/")
class PluginView(MethodView):
    """Returns plugin metadata."""

    @FILES_BLP.response(HTTPStatus.OK, PluginMetadataSchema())
    def get(self):
        plugin = FilesMakerPlugin.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        return PluginMetadata(
            title=plugin.name,
            description=plugin.description,
            name=plugin.name,
            version=plugin.version,
            type=PluginType.processing,
            entry_point=EntryPoint(
                href=url_for(f"{FILES_BLP.name}.ProcessView"),
                ui_href=url_for(f"{FILES_BLP.name}.MicroFrontend"),
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
                        data_type="text/plain",
                        content_type=["text/x-qasm"],
                        required=True,
                        name="circuit.qasm",
                    ),
                    OutputDataMetadata(
                        data_type="application/json",
                        content_type=["application/json"],
                        required=True,
                        name="metadata.json",
                    ),
                ],
            ),
            tags=plugin.tags,
        )


@FILES_BLP.route("/ui/")
class MicroFrontend(MethodView):
    """A basic UI for submitting two text inputs to be stored as files."""

    @FILES_BLP.html_response(HTTPStatus.OK, description="Files Maker plugin UI (GET).")
    @FILES_BLP.arguments(
        TextsToFilesParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="query",
        required=False,
    )
    def get(self, errors):
        return self.render(request.args, errors, valid=False)

    @FILES_BLP.html_response(HTTPStatus.OK, description="Files Maker plugin UI (POST).")
    @FILES_BLP.arguments(
        TextsToFilesParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="form",
        required=False,
    )
    def post(self, errors):
        return self.render(request.form, errors, valid=(not errors))

    def render(self, data: Mapping, errors: dict, valid: bool):
        plugin = FilesMakerPlugin.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        schema = TextsToFilesParametersSchema()
        return Response(
            render_template(
                "simple_template.html",
                name=plugin.name,
                version=plugin.version,
                schema=schema,
                valid=valid,
                values=data,
                errors=errors,
                process=url_for(f"{FILES_BLP.name}.ProcessView"),
                help_text="Provide QASM code and metadata. The result is two separate files.",
            )
        )


@FILES_BLP.route("/process/")
class ProcessView(MethodView):
    """Starts the Celery task that stores text inputs as files."""

    @FILES_BLP.arguments(TextsToFilesParametersSchema(unknown=EXCLUDE), location="form")
    @FILES_BLP.response(HTTPStatus.SEE_OTHER)
    def post(self, arguments):
        db_task = ProcessingTask(
            task_name=store_texts_task.name, parameters=dumps(arguments)
        )
        db_task.save(commit=True)

        task: chain = store_texts_task.s(db_id=db_task.id) | save_task_result.s(
            db_id=db_task.id
        )
        task.link_error(save_task_error.s(db_id=db_task.id))
        task.apply_async()

        db_task.save(commit=True)

        return redirect(
            url_for("tasks-api.TaskView", task_id=str(db_task.id)),
            HTTPStatus.SEE_OTHER,
        )
