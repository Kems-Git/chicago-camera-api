import json
import logging

import azure.functions as func

from camera_api.cosmos_client import get_all_cameras, upsert_cameras
from camera_api.geo import haversine_distance_m
from camera_api.socrata_client import fetch_speed_cameras
from camera_api.staleness import is_stale

DEFAULT_RADIUS_METERS = 3000

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


def _error_response(message: str, status_code: int) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"error": message}), status_code=status_code, mimetype="application/json"
    )


@app.route(route="cameras/nearby")
def get_nearby_cameras(req: func.HttpRequest) -> func.HttpResponse:
    lat_raw = req.params.get("lat")
    lon_raw = req.params.get("lon")
    radius_raw = req.params.get("radius_m", str(DEFAULT_RADIUS_METERS))

    if lat_raw is None or lon_raw is None:
        return _error_response("lat and lon query parameters are required", 400)

    try:
        lat = float(lat_raw)
        lon = float(lon_raw)
        radius_m = float(radius_raw)
    except ValueError:
        return _error_response("lat, lon, and radius_m must be numeric", 400)

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return _error_response("lat must be in [-90, 90] and lon must be in [-180, 180]", 400)

    nearby = []
    for camera in get_all_cameras():
        distance_m = haversine_distance_m(lat, lon, camera["latitude"], camera["longitude"])
        if distance_m <= radius_m:
            nearby.append(
                {
                    "id": camera["id"],
                    "address": camera.get("address"),
                    "latitude": camera["latitude"],
                    "longitude": camera["longitude"],
                    "distance_m": round(distance_m, 1),
                    "go_live_date": camera.get("go_live_date"),
                    "is_stale": is_stale(camera.get("go_live_date")),
                }
            )

    nearby.sort(key=lambda c: c["distance_m"])

    response = {
        "query": {"lat": lat, "lon": lon, "radius_m": radius_m},
        "count": len(nearby),
        "cameras": nearby,
    }
    if not nearby:
        response["message"] = f"No known cameras within {int(radius_m)}m of the provided location."

    return func.HttpResponse(json.dumps(response), mimetype="application/json")
