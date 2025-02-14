import json
import struct
from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import are_vectors_orthogonal
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.requests import open_url
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisOrthogonality

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisOrthogonality.instance.identifier}.orthogonality_task",
    bind=True,
)
def orthogonality_task(self, db_id: int) -> str:
    """
    Retrieves either:
      - two vectors from the parameters, or
      - a .qcd circuit descriptor,
    and checks if the resulting states are orthogonal.
    """

    TASK_LOGGER.info(f"Starting 'orthogonality' task with DB ID '{db_id}'.")

    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"No task data found for ID {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    params = loads(task_data.parameters or "{}")
    TASK_LOGGER.info(f"Parameters: {params}")

    vectors = params.get("vectors")
    circuit_url = params.get("circuit")
    prob_tol = params.get("probability_tolerance") or 1e-5
    inner_tol = params.get("innerproduct_tolerance") or 1e-10

    try:
        if vectors is not None:
            # CASE A: Direct vectors
            new_vectors = []
            for vector in vectors:
                comps = [complex(r, i) for (r, i) in vector]
                new_vectors.append(np.array(comps))
            if len(new_vectors) != 2:
                raise ValueError("Exactly two vectors are required for orthogonality.")

            vec1, vec2 = new_vectors

        elif circuit_url is not None:
            # CASE B: Circuit descriptor
            with open_url(circuit_url) as resp:
                qasm_code = resp.text

            statevector = [[1, 0], [1, 0]]

            if len(statevector) != 2:
                raise ValueError("Decoded data must contain exactly two vectors.")

            # TODO Finish here
            decoded_vectors = []
            vec1 = np.array(decoded_vectors[0])
            vec2 = np.array(decoded_vectors[1])

        else:
            raise ValueError(
                "No valid input found. Provide either 'vectors' or 'circuit'."
            )

        # Check orthogonality
        result = are_vectors_orthogonal(vec1, vec2, tolerance=inner_tol)
        output_data = {
            "result": bool(result),
            "vectorsUsed": 2,
            "inputType": "vectors" if vectors else "circuit",
        }

        # Store results

        with SpooledTemporaryFile(mode="w") as json_file:
            json.dump(output_data, json_file)
            json_file.seek(0)
            STORE.persist_task_result(
                db_id,
                json_file,
                "out.json",
                "custom/orthogonality-output",
                "application/json",
            )

        TASK_LOGGER.info(f"Orthogonality check completed: {output_data}")
        return json.dumps(output_data)

    except Exception as e:
        TASK_LOGGER.error(f"Error in orthogonality task: {e}")
        raise
