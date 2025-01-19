import json
from collections import deque
from json import loads
from tempfile import SpooledTemporaryFile

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import are_vectors_orthogonal
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisOrthogonalPartitioningResistant

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisOrthogonalPartitioningResistant.instance.identifier}.orthogonal_partitioning_resistant_task",
    bind=True,
)
def orthogonal_partitioning_resistant_task(self, db_id: int) -> str:
    TASK_LOGGER.info(
        f"Starting 'orthogonal_partitioning_resistant_task' with db_id={db_id}"
    )

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

    n = len(np_vectors)
    if n == 0:
        # Leere Liste => trivialerweise "zusammenhängend" (oder false?).
        # Hier: wir nehmen an, leer => True
        output_data = {"result": True}
        return _store_and_return_result(db_id, output_data)

    # Erstelle Adjazenzliste: Kante, wenn orthogonal
    adjacency = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if are_vectors_orthogonal(np_vectors[i], np_vectors[j], tolerance):
                adjacency[i].append(j)
                adjacency[j].append(i)

    # Prüfe per BFS oder DFS, ob der Graph zusammenhängend ist
    visited = set()
    queue = deque([0])
    visited.add(0)

    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    all_connected = len(visited) == n

    output_data = {"result": bool(all_connected)}
    return _store_and_return_result(db_id, output_data)


def _store_and_return_result(db_id: int, output_data: dict) -> str:
    """Hilfsfunktion, um das Ergebnis als TXT/JSON zu speichern und zurückzugeben."""
    with SpooledTemporaryFile(mode="w") as txt_file:
        txt_file.write(str(output_data))
        txt_file.seek(0)
        STORE.persist_task_result(
            db_id,
            txt_file,
            "out.txt",
            "custom/orthogonal-partitioning-output",
            "text/plain",
        )

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
