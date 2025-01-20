import json
from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import are_vectors_linearly_dependent
from common.encoding_registry import EncodingRegistry
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.requests import open_url
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisLineardependence

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisLineardependence.instance.identifier}.lineardependence_task",
    bind=True,
)
def lineardependence_task(self, db_id: int) -> str:
    """
    Either takes multiple vectors or decodes them from a circuit descriptor,
    then checks for linear dependence.
    """

    TASK_LOGGER.info(f"Starting 'lineardependence' task with DB ID='{db_id}'.")

    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"No task data found for ID {db_id}."
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    params = loads(task_data.parameters or "{}")
    TASK_LOGGER.info(f"Parameters: {params}")

    vectors = params.get("vectors")
    tolerance = params.get("tolerance") or 1e-10
    circuit_url = params.get("circuit")
    prob_tol = params.get("probability_tolerance") or 1e-5

    try:
        if vectors is not None:
            # CASE A: direct vectors
            np_vectors = []
            for v in vectors:
                arr = np.array([complex(re, im) for (re, im) in v])
                np_vectors.append(arr)

        elif circuit_url is not None:
            # CASE B: decode from QCD
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

            # decoded is a list of vectors
            np_vectors = []
            for vector in decoded:
                arr = np.array(vector, dtype=complex)
                np_vectors.append(arr)
        else:
            raise ValueError("No valid input provided.")

        # Now call are_vectors_linearly_dependent
        result = are_vectors_linearly_dependent(np_vectors, tolerance=tolerance)

        output_data = {
            "result": bool(result),
            "inputType": "vectors" if vectors else "circuit",
        }

        # Save results
        with SpooledTemporaryFile(mode="w") as json_file:
            json.dump(output_data, json_file)
            json_file.seek(0)
            STORE.persist_task_result(
                db_id,
                json_file,
                "out.json",
                "custom/lineardependence-output",
                "application/json",
            )

        TASK_LOGGER.info(f"Lineardependence result: {output_data}")
        return json.dumps(output_data)

    except Exception as e:
        TASK_LOGGER.error(f"Error in 'lineardependence' task: {e}")
        raise
