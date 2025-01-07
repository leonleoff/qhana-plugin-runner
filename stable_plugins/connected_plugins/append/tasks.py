from tempfile import SpooledTemporaryFile
from typing import Optional
from json import loads

from celery.utils.log import get_task_logger
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.storage import STORE

from . import AppendPlugin

TASK_LOGGER = get_task_logger(__name__)

@CELERY.task(name=f"{AppendPlugin.instance.identifier}.append_task", bind=True)
def append_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting append task with db id '{db_id}'")
    task_data = ProcessingTask.get_by_id(id_=db_id)

    if not task_data:
        msg = f"Could not load task data with id {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    input_text = parameters.get("inputText", "")

    TASK_LOGGER.info(f"Input text: {input_text}")

    try:
        # Append "world" to the input text
        output_text = f"{input_text} world"
        TASK_LOGGER.info(f"Appended text: {output_text}")

        # Save the result
        with SpooledTemporaryFile(mode="w") as output:
            output.write(output_text)
            output.seek(0)
            STORE.persist_task_result(
                db_id,
                output,
                "output.txt",  # Filename
                "custom/append-output",  # Data type
                "text/plain",  # Content type
            )

        return output_text

    except Exception as e:
        TASK_LOGGER.error(f"Error in append task: {e}")
        raise
