import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from azure.cosmos import CosmosClient
from azure.cosmos.container import ContainerProxy


@lru_cache(maxsize=1)
def _client() -> CosmosClient:
    endpoint = os.environ["COSMOS_ENDPOINT"]
    key = os.environ["COSMOS_KEY"]
    return CosmosClient(endpoint, credential=key)


def _database():
    database_name = os.environ["COSMOS_DATABASE"]
    return _client().get_database_client(database_name)


def cameras_container() -> ContainerProxy:
    return _database().get_container_client("cameras")


def query_logs_container() -> ContainerProxy:
    return _database().get_container_client("query_logs")


def upsert_cameras(cameras: list[dict]) -> None:
    container = cameras_container()
    seen_at = datetime.now(timezone.utc).isoformat()
    for camera in cameras:
        container.upsert_item(
            {
                **camera,
                "status": "active",
                "last_seen_at": seen_at,
                "decommissioned_at": None,
            }
        )


def get_all_cameras() -> list[dict]:
    container = cameras_container()
    return list(
        container.query_items(
            query="SELECT * FROM c WHERE c.status = 'active'",
            enable_cross_partition_query=True,
        )
    )


def get_decommissioned_cameras() -> list[dict]:
    container = cameras_container()
    return list(
        container.query_items(
            query="SELECT * FROM c WHERE c.status = 'decommissioned'",
            enable_cross_partition_query=True,
        )
    )


def mark_decommissioned_cameras(grace_days: int = 7) -> list[str]:
    container = cameras_container()
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=grace_days)).isoformat()

    stale = container.query_items(
        query=(
            "SELECT * FROM c "
            "WHERE (NOT IS_DEFINED(c.status) OR c.status != 'decommissioned') "
            "AND (NOT IS_DEFINED(c.last_seen_at) OR c.last_seen_at < @cutoff)"
        ),
        parameters=[{"name": "@cutoff", "value": cutoff}],
        enable_cross_partition_query=True,
    )

    marked = []
    for camera in stale:
        container.upsert_item(
            {**camera, "status": "decommissioned", "decommissioned_at": now.isoformat()}
        )
        marked.append(camera["id"])

    return marked


def log_query(endpoint: str, lat: str | None, lon: str | None) -> None:
    now = datetime.now(timezone.utc)
    try:
        query_logs_container().create_item(
            {
                "id": str(uuid.uuid4()),
                "logDate": now.strftime("%Y-%m-%d"),
                "endpoint": endpoint,
                "lat": lat,
                "lon": lon,
                "timestamp": now.isoformat(),
            }
        )
    except Exception as error:
        logging.warning("Failed to write query log: %s", error)
