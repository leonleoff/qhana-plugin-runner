import json
from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

from celery.utils.log import get_task_logger
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.storage import STORE

from . import FilesMakerPlugin

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(name=f"{FilesMakerPlugin.instance.identifier}.store_texts_task", bind=True)
def store_texts_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting text-storing task with db_id={db_id}")

    task_data: Optional[ProcessingTask] = ProcessingTask.get_by_id(db_id)
    if not task_data:
        msg = f"No task data found for DB ID {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    try:
        parameters = loads(task_data.parameters or "{}")
        qasm_code = parameters.get("qasmCode")
        meta_data = parameters.get("metaData")
        if not qasm_code:
            raise ValueError("Missing required parameter: 'qasmCode'")
        if not meta_data:
            raise ValueError("Missing required parameter: 'metaData'")
    except (json.JSONDecodeError, ValueError) as e:
        TASK_LOGGER.error(f"Error parsing task parameters: {e}")
        raise ValueError(f"Invalid parameters: {e}")

    try:
        with SpooledTemporaryFile(mode="w") as output:
            output.write(qasm_code)
            STORE.persist_task_result(
                db_id,
                output,
                "circuit.qasm",
                "custom/filesMaker-output",
                "text/x-qasm",
            )
        TASK_LOGGER.info("QASM file successfully stored.")
    except Exception as e:
        TASK_LOGGER.error(f"Error storing QASM file: {e}")
        raise

    try:
        with SpooledTemporaryFile(mode="w") as output:
            json.dump(meta_data, output, indent=4)
            output.seek(0)
            STORE.persist_task_result(
                db_id,
                output,
                "metadata.json",
                "custom/filesMaker-output",
                "application/json",
            )
        TASK_LOGGER.info("Metadata file successfully stored.")
    except Exception as e:
        TASK_LOGGER.error(f"Error storing metadata JSON: {e}")
        raise

    TASK_LOGGER.info("Task completed successfully.")
    return "Files created successfully."
