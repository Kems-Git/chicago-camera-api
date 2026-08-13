import logging
import time

from sodapy import Socrata

SPEED_CAMERA_DATASET_ID = "4i42-qv3h"
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (2, 4, 8)


def fetch_speed_cameras() -> list[dict]:
    client = Socrata("data.cityofchicago.org", None)

    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            rows = client.get(SPEED_CAMERA_DATASET_ID, limit=1000)
            return [_normalize(row) for row in rows if "latitude" in row and "longitude" in row]
        except Exception as error:  # noqa: BLE001 - deliberately broad, see retry loop below
            last_error = error
            logging.warning("Socrata fetch attempt %d failed: %s", attempt + 1, error)
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(BACKOFF_SECONDS[attempt])

    raise last_error


def _normalize(row: dict) -> dict:
    return {
        "id": f"speed_camera:{row.get('location_id', row.get('id'))}",
        "type": "speed_camera",
        "location_id": row.get("location_id"),
        "address": row.get("address"),
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        "go_live_date": row.get("go_live_date"),
        "first_approach": row.get("first_approach"),
        "second_approach": row.get("second_approach"),
    }
