import json
from json import loads
from tempfile import SpooledTemporaryFile

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import are_vectors_orthogonal
from common.encoding_registry import EncodingRegistry
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.requests import open_url
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisPairwiseOrthogonality

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisPairwiseOrthogonality.instance.identifier}.pairwise_orthogonality_task",
    bind=True,
)
def pairwise_orthogonality_task(self, db_id: int) -> str:
    """
    Checks if all vectors in a set are pairwise orthogonal, or decodes them
    from a .qcd circuit descriptor and then does the same check.
    """

    TASK_LOGGER.info(f"Starting 'pairwise_orthogonality_task' with db_id={db_id}")

    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"No task data found for ID {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    vectors = parameters.get("vectors")
    tolerance = parameters.get("tolerance") or 1e-10
    circuit_url = parameters.get("circuit")
    prob_tol = parameters.get("probability_tolerance") or 1e-5

    TASK_LOGGER.info(
        f"Parameters: vectors={vectors}, circuit={circuit_url}, tolerance={tolerance}"
    )

    try:
        if vectors is not None:
            # CASE A: direct vectors
            np_vectors = []
            for vec in vectors:
                cnums = [complex(r, i) for (r, i) in vec]
                np_vectors.append(np.array(cnums))

        elif circuit_url is not None:
            # CASE B: decode from circuit
            with open_url(circuit_url) as resp:
                qcd_data = json.loads(resp.text)
            qasm_code = qcd_data["circuit"]
            divisions = qcd_data["metadata"]["circuit_divisions"]
            strategy_id = qcd_data["metadata"]["strategy_id"]

            strategy = EncodingRegistry.get_strategy(strategy_id)
            decoded = strategy.decode(
                qasm_code, divisions, {"probability_tolerance": prob_tol}
            )
            np_vectors = [np.array(vec, dtype=complex) for vec in decoded]

        else:
            raise ValueError("No valid input found for pairwise orthogonality plugin.")

        # Check each pair for orthogonality
        all_orthogonal = True
        n = len(np_vectors)
        for i in range(n):
            for j in range(i + 1, n):
                if not are_vectors_orthogonal(np_vectors[i], np_vectors[j], tolerance):
                    all_orthogonal = False
                    break
            if not all_orthogonal:
                break

        output_data = {"result": bool(all_orthogonal)}

        # Save results

        with SpooledTemporaryFile(mode="w") as json_file:
            json.dump(output_data, json_file)
            json_file.seek(0)
            STORE.persist_task_result(
                db_id,
                json_file,
                "out.json",
                "custom/pairwise-orthogonality-output",
                "application/json",
            )

        TASK_LOGGER.info(f"Pairwise Orthogonality result: {output_data}")
        return json.dumps(output_data)

    except Exception as e:
        TASK_LOGGER.error(f"Error in pairwise_orthogonality_task: {e}")
        raise
