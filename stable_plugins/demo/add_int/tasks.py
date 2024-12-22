from tempfile import SpooledTemporaryFile

from typing import Optional
from json import loads

from celery.utils.log import get_task_logger

from . import HelloWorldMultiStep
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask

from qhana_plugin_runner.storage import STORE

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{HelloWorldMultiStep.instance.identifier}.preprocessing_task", bind=True
)
def preprocessing_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting preprocessing demo task with db id '{db_id}'")
    task_data: Optional[ProcessingTask] = ProcessingTask.get_by_id(id_=db_id)
    TASK_LOGGER.info("6969")

    if task_data is None:
        msg = f"Could not load task data with id {db_id} to read parameters!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)
    # Load input parameters
    parameters = loads(task_data.parameters or "{}")
    input_int1: Optional[int] = parameters.get("input_int1", None)
    input_int2: Optional[int] = parameters.get("input_int2", None)
    TASK_LOGGER.info(f"Loaded input parameters from db: input_int1='{input_int1}', input_int2='{input_int2}'")

    # Validate input parameters
    if input_int1 is None or input_int2 is None:
        raise ValueError("Missing input parameters for input_int1 or input_int2!")

    # Perform preprocessing
    sum_result = input_int1 + input_int2
    TASK_LOGGER.info(f"Calculated sum: {sum_result}")

    # Save result to task data
    task_data.data["sum_result"] = sum_result
    task_data.save(commit=True)

    # Save output to file and persist it
    out_str = f"Processed integers: {input_int1} + {input_int2} = {sum_result}"
    with SpooledTemporaryFile(mode="w") as output:
        output.write(out_str)
        STORE.persist_task_result(
            db_id, output, "output1.txt", "integer-sum-output", "text/plain"
        )

    return f"Preprocessing completed with result: {out_str}"


@CELERY.task(name=f"{HelloWorldMultiStep.instance.identifier}.processing_task", bind=True)
def processing_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting processing demo task with db id '{db_id}'")
    task_data: Optional[ProcessingTask] = ProcessingTask.get_by_id(id_=db_id)

    if task_data is None:
        msg = f"Could not load task data with id {db_id} to read parameters!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    input_str: Optional[str] = loads(task_data.parameters or "{}").get("input_str", None)
    TASK_LOGGER.info(f"Loaded input parameters from db: input_str='{input_str}'")
    if input_str is None:
        raise ValueError("No input argument provided!")

    try:
        input_str_preprocessing = task_data.data["input_str"]
    except:
        input_str_preprocessing = ""

    if input_str:
        out_str = (
            "Processed in the processing step: "
            + input_str_preprocessing
            + " "
            + input_str
        )
        with SpooledTemporaryFile(mode="w") as output:
            output.write(out_str)
            STORE.persist_task_result(
                db_id, output, "output2.txt", "hello-world-output", "text/plain"
            )
        return "result: " + repr(out_str)
    return "Empty input string, no output could be generated!"
