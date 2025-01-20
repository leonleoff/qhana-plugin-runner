import json
import struct
from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import are_vectors_orthogonal
from encoding_strategies.encoding_registry import EncodingRegistry
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.requests import get_mimetype, open_url
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisOrthogonality

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisOrthogonality.instance.identifier}.orthogonality_task",
    bind=True,
)
def orthogonality_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting 'orthogonality' task with database ID '{db_id}'.")

    # load
    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"Task data with ID {db_id} could not be loaded!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    TASK_LOGGER.info(f"Parameters: {parameters}")

    # read from parameters
    vectors = parameters.get("vectors")  # e.g. [ [ [re,im], ... ], [ [re,im], ... ] ]
    circuit = parameters.get("circuit")  # e.g. "some://url"
    prob_tol = parameters.get("probability_tolerance") or 1e-5
    inner_tol = parameters.get("innerproduct_tolerance") or 1e-10

    try:
        if vectors is not None:
            # "vectors" is set of two complex vectors
            # transform to numpy
            new_set_of_vectors = []
            for vector in vectors:
                complex_numbers = [complex(pair[0], pair[1]) for pair in vector]
                new_set_of_vectors.append(np.array(complex_numbers))

            if len(new_set_of_vectors) != 2:
                raise ValueError(
                    "Exactly two vectors are required for orthogonality check!"
                )
            vec1, vec2 = new_set_of_vectors

        elif circuit is not None:
            # Fetch the circuit data using open_url
            with open_url(circuit) as circuit_response:
                content = circuit_response.text

            # Parse the QuantumCircuitDescriptor (.qcd) content
            qcd_data = json.loads(content)
            qasm_code = qcd_data["circuit"]
            metadata = qcd_data["metadata"]

            # Extract relevant metadata
            strategy_id = metadata["strategy_id"]
            circuit_divisions = metadata["circuit_divisions"]
            # TODO: Let choose
            # Ensure the encoding strategy is supported (hardcoded for now)
            if strategy_id != "split_complex_binary_encoding":
                raise ValueError(
                    f"Unsupported encoding strategy: {strategy_id}. Expected 'split_complex_binary_encoding'."
                )

            # Decode the vectors using the provided QASM and circuit divisions
            strategy = EncodingRegistry.get_strategy(strategy_id)

            # Prepare the options dictionary
            options = {"probability_tolerance": prob_tol}

            # Pass the options dictionary to the decode method
            decoded_vectors = strategy.decode(
                qasm_code, circuit_divisions, options=options
            )

            # Validate the decoded vectors
            if len(decoded_vectors) != 2:
                raise ValueError(
                    "Circuit must decode exactly two vectors for orthogonality check!"
                )

            vec1 = np.array(decoded_vectors[0])
            vec2 = np.array(decoded_vectors[1])
        else:
            raise ValueError("Neither vectors nor circuit input found!")

        # now do are_vectors_orthogonal
        result = are_vectors_orthogonal(vec1, vec2, tolerance=inner_tol)

        # Build output
        output_data = {
            "result": bool(result),
            "vectorsUsed": 2,
            "inputType": "vectors" if vectors else "circuit",
        }

        # persist
        with SpooledTemporaryFile(mode="w") as txt_file:
            txt_file.write(str(output_data))
            txt_file.seek(0)
            STORE.persist_task_result(
                db_id,
                txt_file,
                "out.txt",
                "custom/orthogonality-output",
                "text/plain",
            )

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

        TASK_LOGGER.info(f"Orthogonality result: {output_data}")
        return json.dumps(output_data)

    except Exception as e:
        TASK_LOGGER.error(f"Error in orthogonality task: {e}")
        raise
