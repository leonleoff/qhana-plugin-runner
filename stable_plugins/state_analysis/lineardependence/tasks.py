from tempfile import SpooledTemporaryFile

from typing import Optional
from json import loads

from celery.utils.log import get_task_logger

import numpy as np

from .algorithm import are_vectors_orthogonal
from . import ClassicalStateAnalysisLineardependence
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask

from qhana_plugin_runner.storage import STORE

TASK_LOGGER = get_task_logger(__name__)

@CELERY.task(name=f"{ClassicalStateAnalysisLineardependence.instance.identifier}.lineardependence_task", bind=True)
def lineardependence_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting lineardependence task with db id '{db_id}'")
    task_data = ProcessingTask.get_by_id(id_=db_id)

    if not task_data:
        msg = f"Could not load task data with id {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    vector1 = parameters.get("vector1", [])
    vector2 = parameters.get("vector2", [])
    tolerance = parameters.get("tolerance", 1e-10)

    TASK_LOGGER.info(f"Parameters: vector1={vector1}, vector2={vector2}, tolerance={tolerance}")

    try:
        vec1 = np.array(vector1, dtype=float)
        vec2 = np.array(vector2, dtype=float)

        result = are_vectors_orthogonal(vec1,vec2,tolerance)
        output_message = "Vectors are linearly dependent." if result else "Vectors are not linearly dependent."

        # Speichere das Ergebnis als Datei
        with SpooledTemporaryFile(mode="w") as output:
            output.write(output_message)
            output.seek(0)  # Datei-Pointer zurücksetzen
            STORE.persist_task_result(
                db_id,
                output,
                "out.txt",  # Dateiname
                "custom/lineardependence-output",  # Datentyp
                "text/plain",  # Content-Type
            )

        return output_message

    except Exception as e:
        TASK_LOGGER.error(f"Error in lineardependence task: {e}")
        raise
