import os
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
    for camera in cameras:
        container.upsert_item(camera)


def get_all_cameras() -> list[dict]:
    container = cameras_container()
    return list(
        container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True)
    )
