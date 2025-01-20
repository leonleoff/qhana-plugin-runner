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
    ORTHOGONAL_PARTITIONING_RESISTANT_BLP,
    ClassicalStateAnalysisOrthogonalPartitioningResistant,
)
from .schemas import OrthogonalPartitioningResistantParametersSchema
from .tasks import orthogonal_partitioning_resistant_task


@ORTHOGONAL_PARTITIONING_RESISTANT_BLP.route("/")
class PluginsView(MethodView):
    """Returns plugin metadata for orthogonal partitioning resistant."""

    @ORTHOGONAL_PARTITIONING_RESISTANT_BLP.response(HTTPStatus.OK, PluginMetadataSchema())
    def get(self):
        plugin = ClassicalStateAnalysisOrthogonalPartitioningResistant.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        return PluginMetadata(
            title=plugin.name,
            description=plugin.description,
            name=plugin.name,
            version=plugin.version,
            type=PluginType.processing,
            entry_point=EntryPoint(
                href=url_for(f"{ORTHOGONAL_PARTITIONING_RESISTANT_BLP.name}.ProcessView"),
                ui_href=url_for(
                    f"{ORTHOGONAL_PARTITIONING_RESISTANT_BLP.name}.MicroFrontend"
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
                        data_type="custom/orthogonal-partitioning-output",
                        content_type=["text/plain"],
                        required=True,
                    )
                ],
            ),
            tags=plugin.tags,
        )


@ORTHOGONAL_PARTITIONING_RESISTANT_BLP.route("/ui/")
class MicroFrontend(MethodView):
    """
    UI for checking if the entire set of vectors is in one connected component (via orthonormal edges).
    Now also supporting circuit input.
    """

    example_vectors = [
        [[1.0, 0.0], [0.0, 0.0]],
        [[0.0, 0.0], [1.0, 0.0]],
        [[1.0, 0.0], [1.0, 0.0]],
    ]
    example_inputs = {
        "vectors": f"{example_vectors}",
        "tolerance": "1e-10",
    }

    @ORTHOGONAL_PARTITIONING_RESISTANT_BLP.html_response(
        HTTPStatus.OK, description="Orthogonal partitioning plugin UI (GET)."
    )
    @ORTHOGONAL_PARTITIONING_RESISTANT_BLP.arguments(
        OrthogonalPartitioningResistantParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="query",
        required=False,
    )
    def get(self, errors):
        return self.render(request.args, errors, valid=False)

    @ORTHOGONAL_PARTITIONING_RESISTANT_BLP.html_response(
        HTTPStatus.OK, description="Orthogonal partitioning plugin UI (POST)."
    )
    @ORTHOGONAL_PARTITIONING_RESISTANT_BLP.arguments(
        OrthogonalPartitioningResistantParametersSchema(
            partial=True, unknown=EXCLUDE, validate_errors_as_result=True
        ),
        location="form",
        required=False,
    )
    def post(self, errors):
        return self.render(request.form, errors, valid=(not errors))

    def render(self, data: Mapping, errors: dict, valid: bool):
        plugin = ClassicalStateAnalysisOrthogonalPartitioningResistant.instance
        if plugin is None:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

        schema = OrthogonalPartitioningResistantParametersSchema()
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
                    f"{ORTHOGONAL_PARTITIONING_RESISTANT_BLP.name}.ProcessView"
                ),
                help_text="Check if all vectors form one connected component. Now also supports .qcd circuit input.",
                example_values=url_for(
                    f"{ORTHOGONAL_PARTITIONING_RESISTANT_BLP.name}.MicroFrontend",
                    **self.example_inputs,
                ),
            )
        )


@ORTHOGONAL_PARTITIONING_RESISTANT_BLP.route("/process/")
class ProcessView(MethodView):
    """
    Starts the orthogonal-partitioning-resistant task.
    """

    @ORTHOGONAL_PARTITIONING_RESISTANT_BLP.arguments(
        OrthogonalPartitioningResistantParametersSchema(unknown=EXCLUDE),
        location="form",
    )
    @ORTHOGONAL_PARTITIONING_RESISTANT_BLP.response(HTTPStatus.SEE_OTHER)
    def post(self, arguments):
        db_task = ProcessingTask(
            task_name=orthogonal_partitioning_resistant_task.name,
            parameters=dumps(arguments),
        )
        db_task.save(commit=True)

        task_chain = orthogonal_partitioning_resistant_task.s(
            db_id=db_task.id
        ) | save_task_result.s(db_id=db_task.id)
        task_chain.link_error(save_task_error.s(db_id=db_task.id))
        task_chain.apply_async()

        db_task.save(commit=True)

        return redirect(
            url_for("tasks-api.TaskView", task_id=str(db_task.id)),
            code=HTTPStatus.SEE_OTHER,
        )
