import json
from json import loads
from tempfile import SpooledTemporaryFile

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import are_vectors_orthogonal
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisPairwiseNonOrthogonality

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisPairwiseNonOrthogonality.instance.identifier}.pairwise_non_orthogonality_task",
    bind=True,
)
def pairwise_non_orthogonality_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting 'pairwise_non_orthogonality_task' with db_id={db_id}")

    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"No task data found for ID {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    vectors = parameters.get("vectors", [])
    tolerance = parameters.get("tolerance")

    TASK_LOGGER.info(f"Parameters: vectors={vectors}, tolerance={tolerance}")

    # Transform into numpy arrays
    np_vectors = []
    try:
        for vec in vectors:
            complex_numbers = [complex(r, i) for (r, i) in vec]
            np_vectors.append(np.array(complex_numbers))
    except Exception as e:
        TASK_LOGGER.error(f"Error creating NumPy arrays: {e}")
        raise

    # Check pairwise orthogonality
    all_orthogonal = True
    n = len(np_vectors)
    for i in range(n):
        for j in range(i + 1, n):
            # Wenn ein Paar NICHT orthogonal ist, brechen wir ab
            if not are_vectors_orthogonal(np_vectors[i], np_vectors[j], tolerance):
                all_orthogonal = False
                break
        if not all_orthogonal:
            break

    # Result: True = alle orthogonal, False = min. ein Paar nicht orthogonal
    output_data = {
        "result": bool(all_orthogonal),
    }

    # Persist results
    with SpooledTemporaryFile(mode="w") as txt_file:
        txt_file.write(str(output_data))
        txt_file.seek(0)
        STORE.persist_task_result(
            db_id,
            txt_file,
            "out.txt",
            "custom/pairwise-non-orthogonality-output",
            "text/plain",
        )

    with SpooledTemporaryFile(mode="w") as json_file:
        json.dump(output_data, json_file)
        json_file.seek(0)
        STORE.persist_task_result(
            db_id,
            json_file,
            "out.json",
            "custom/pairwise-non-orthogonality-output",
            "application/json",
        )

    TASK_LOGGER.info(f"Pairwise Non-Orthogonality result: {output_data}")

    return json.dumps(output_data)
