import json
from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import compute_schmidt_rank
from common.encoding_registry import EncodingRegistry
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.requests import open_url
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisSchmidtrank

TASK_LOGGER = get_task_logger(__name__)


def validate_decoded(decoded):

    if not isinstance(decoded, list):
        raise ValueError("Decoded data must be a list.")

    if all(isinstance(element, complex) for element in decoded):
        return True
    elif all(isinstance(element, list) for element in decoded):
        raise ValueError("Decoded data cannot be a list of lists.")
    else:
        raise ValueError(
            "Decoded data must be either a list of complex numbers or a list of lists."
        )


@CELERY.task(
    name=f"{ClassicalStateAnalysisSchmidtrank.instance.identifier}.schmidtrank_task",
    bind=True,
)
def schmidtrank_task(self, db_id: int) -> str:
    """
    Either uses a direct vector + dimA, dimB, or decodes one vector from a .qcd,
    then computes the Schmidt rank.
    """

    TASK_LOGGER.info(f"Starting 'schmidtrank' task with DB ID='{db_id}'.")

    task_data = ProcessingTask.get_by_id(db_id)
    if not task_data:
        msg = f"No task data found for ID {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    params = loads(task_data.parameters or "{}")
    TASK_LOGGER.info(f"Parameters: {params}")

    vector_data = params.get("vector")
    dimA = params.get("dimA")
    dimB = params.get("dimB")
    tolerance = params.get("tolerance") or 1e-10

    circuit_url = params.get("circuit")
    prob_tol = params.get("probability_tolerance") or 1e-5

    try:
        if vector_data is not None:
            # CASE A: direct vector
            cnums = [complex(r, i) for (r, i) in vector_data]
            np_vector = np.array(cnums, dtype=complex)

            result_int = compute_schmidt_rank(np_vector, dimA, dimB, tolerance)

        elif circuit_url is not None:
            # CASE B: decode from circuit
            with open_url(circuit_url) as resp:
                qcd_content = resp.text
            qcd_data = json.loads(qcd_content)
            qasm_code = qcd_data["circuit"]
            divisions = qcd_data["metadata"]["circuit_divisions"]
            strategy_id = qcd_data["metadata"]["strategy_id"]

            strategy = EncodingRegistry.get_strategy(strategy_id)
            decoded = strategy.decode(
                qasm_code, divisions, options={"probability_tolerance": prob_tol}
            )
            TASK_LOGGER.info(f"decoded: {decoded}")

            validate_decoded(decoded)

            if not decoded:
                raise ValueError("Decoded no vectors from the circuit descriptor.")

            result_int = compute_schmidt_rank(
                np.array(decoded, dtype=complex), dimA, dimB, tolerance
            )

        else:
            raise ValueError("No valid input provided for Schmidt rank plugin.")

        output_data = {"result": int(result_int)}

        # Save
        with SpooledTemporaryFile(mode="w") as json_file:
            json.dump(output_data, json_file)
            json_file.seek(0)
            STORE.persist_task_result(
                db_id,
                json_file,
                "out.json",
                "custom/schmidtrank-output",
                "application/json",
            )

        TASK_LOGGER.info(f"Schmidtrank result: {output_data}")
        return json.dumps(output_data)

    except Exception as e:
        TASK_LOGGER.error(f"Error in Schmidtrank task: {e}")
        raise
