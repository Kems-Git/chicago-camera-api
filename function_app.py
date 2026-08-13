import logging

import azure.functions as func

from camera_api.cosmos_client import upsert_cameras
from camera_api.socrata_client import fetch_speed_cameras

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello")
def hello(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("Chicago Camera API is running.")


@app.schedule(schedule="0 0 3 * * *", arg_name="timer", run_on_startup=False)
def poll_camera_data(timer: func.TimerRequest) -> None:
    try:
        cameras = fetch_speed_cameras()
    except Exception as error:
        logging.error("Poll failed after retries, keeping existing cached data: %s", error)
        return

    upsert_cameras(cameras)
    logging.info("Poll succeeded: upserted %d cameras", len(cameras))
