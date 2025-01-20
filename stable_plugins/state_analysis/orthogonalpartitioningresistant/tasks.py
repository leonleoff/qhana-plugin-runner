import json
from collections import deque
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

from . import ClassicalStateAnalysisOrthogonalPartitioningResistant

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisOrthogonalPartitioningResistant.instance.identifier}.orthogonal_partitioning_resistant_task",
    bind=True,
)
def orthogonal_partitioning_resistant_task(self, db_id: int) -> str:
    """
    Either uses multiple vectors or decodes them from a .qcd circuit,
    then builds a graph (edge=orthogonal) and checks connectivity.
    """

    TASK_LOGGER.info(
        f"Starting 'orthogonal_partitioning_resistant_task' with db_id={db_id}"
    )

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
        f"Parameters: vectors={vectors}, circuit={circuit_url}, tol={tolerance}"
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
                qcd_str = resp.text
            qcd_data = json.loads(qcd_str)
            qasm_code = qcd_data["circuit"]
            divisions = qcd_data["metadata"]["circuit_divisions"]
            strategy_id = qcd_data["metadata"]["strategy_id"]

            strategy = EncodingRegistry.get_strategy(strategy_id)
            decoded = strategy.decode(
                qasm_code, divisions, {"probability_tolerance": prob_tol}
            )
            np_vectors = [np.array(vec, dtype=complex) for vec in decoded]
        else:
            raise ValueError("No valid input found. Provide 'vectors' or 'circuit'.")

        n = len(np_vectors)
        if n == 0:
            # If no vectors, we consider it trivially "connected"
            output_data = {"result": True}
            return _store_and_return_result(db_id, output_data)

        # Build adjacency
        adjacency = [[] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                if are_vectors_orthogonal(np_vectors[i], np_vectors[j], tolerance):
                    adjacency[i].append(j)
                    adjacency[j].append(i)

        # BFS for connectivity
        visited = set()
        visited.add(0)
        queue = deque([0])
        while queue:
            curr = queue.popleft()
            for neighbor in adjacency[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        all_connected = len(visited) == n
        output_data = {"result": bool(all_connected)}

        return _store_and_return_result(db_id, output_data)

    except Exception as e:
        TASK_LOGGER.error(f"Error in orthogonal_partitioning_resistant_task: {e}")
        raise


def _store_and_return_result(db_id: int, output_data: dict) -> str:
    """
    Saves the JSON string.
    """

    with SpooledTemporaryFile(mode="w") as json_file:
        json.dump(output_data, json_file)
        json_file.seek(0)
        STORE.persist_task_result(
            db_id,
            json_file,
            "out.json",
            "custom/orthogonal-partitioning-output",
            "application/json",
        )

    TASK_LOGGER.info(f"Orthogonal Partitioning Resistant result: {output_data}")
    return json.dumps(output_data)
