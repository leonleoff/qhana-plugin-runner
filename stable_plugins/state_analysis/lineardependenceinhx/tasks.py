import json
from json import loads
from tempfile import SpooledTemporaryFile

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import analyze_lineardependenceinhx
from common.encoding_registry import EncodingRegistry
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.requests import open_url
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisLineardependenceInHX

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisLineardependenceInHX.instance.identifier}.lineardependenceinhx_task",
    bind=True,
)
def lineardependenceInHX_task(self, db_id: int) -> str:
    """
    Either uses multiple vectors, or .qcd,
    then analyzes linear dependence in a bipartite space using SVD.
    """

    TASK_LOGGER.info(f"Starting 'lineardependenceInHX' task for db_id={db_id}")

    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"No task data found for ID {db_id}"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    params = loads(task_data.parameters or "{}")
    TASK_LOGGER.info(f"Parameters: {params}")

    vectors = params.get("vectors")
    dimA = params.get("dimA")
    dimB = params.get("dimB")
    sv_tol = params.get("singularValueTolerance") or 1e-10
    lin_tol = params.get("linearDependenceTolerance") or 1e-10

    circuit_url = params.get("circuit")
    prob_tol = params.get("probability_tolerance") or 1e-5

    try:
        if vectors is not None:
            # CASE A: direct vectors
            python_vectors = []
            for vec in vectors:
                arr = np.array([complex(r, i) for (r, i) in vec])
                python_vectors.append(arr)

            result_bool = analyze_lineardependenceinhx(
                states=python_vectors,
                dim_A=dimA,
                dim_B=dimB,
                singular_value_tolerance=sv_tol,
                linear_independence_tolerance=lin_tol,
            )

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

            if not decoded:
                raise ValueError("Decoded no vectors from the circuit descriptor.")
            result_bool = analyze_lineardependenceinhx(
                states=[np.array(vec, dtype=complex) for vec in decoded],
                dim_A=dimA,
                dim_B=dimB,
                singular_value_tolerance=sv_tol,
                linear_independence_tolerance=lin_tol,
            )
        else:
            raise ValueError("No valid input provided for lineardependenceInHX plugin.")

        output_data = {"result": bool(result_bool)}

        # Save
        with SpooledTemporaryFile(mode="w") as json_file:
            json.dump(output_data, json_file)
            json_file.seek(0)
            STORE.persist_task_result(
                db_id,
                json_file,
                "out.json",
                "custom/lineardependenceInHX-output",
                "application/json",
            )

        TASK_LOGGER.info(f"lineardependenceInHX result: {output_data}")
        return json.dumps(output_data)

    except Exception as e:
        TASK_LOGGER.error(f"Error in lineardependenceInHX task: {e}")
        raise
