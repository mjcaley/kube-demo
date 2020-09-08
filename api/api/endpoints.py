import uuid

from aiohttp import web
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity
from azure.common import AzureMissingResourceHttpError

from . import __version__


LISTS = "todolist"
ITEMS = "todoitems"


def initialize_db(table_service):
    if not table_service.exists(LISTS):
        table_service.create_table(LISTS)
    if not table_service.exists(ITEMS):
        table_service.create_table(ITEMS)


routes = web.RouteTableDef()


@routes.get("/version")
async def version(request):
    return web.HTTPOk(text=__version__)


@routes.get("/lists")
async def get_lists(request):
    table_service = request.app["connection-string"]
    lists = table_service.query_entities(LISTS)

    return web.json_response({"lists": [item.PartitionKey for item in lists.items]})


@routes.post("/lists")
async def create_list(request: web.Request):
    table_service = request.app["connection-string"]
    body = await request.json()
    table_service.insert_or_merge_entity(LISTS, {"PartitionKey": body["list"]["name"], "RowKey": "list"})

    return web.json_response({"status": "success"})


@routes.get("/lists/{list_id}")
async def list(request):
    table_service = request.app["connection-string"]
    list_id = request.match_info["list_id"]
    items = table_service.query_entities(ITEMS, filter=f"PartitionKey eq '{list_id}'")

    return web.json_response({"items": [{"row_key": item.RowKey, "text": item.text, "done": item.done} for item in items]})


@routes.post("/lists/{list_id}")
async def add_item(request: web.Request):
    table_service = request.app["connection-string"]
    list_id = request.match_info["list_id"]
    body = await request.json()
    row_key = str(uuid.uuid4())

    item = Entity()
    item.PartitionKey = list_id
    item.RowKey = row_key
    item.text = body["text"]
    item.done = False

    table_service.insert_entity(ITEMS, item)

    return web.json_response({"row_key": row_key}, status=201)


@routes.delete("/lists/{list_id}")
async def delete_list(request):
    table_service = request.app["connection-string"]
    list_id = request.match_info["list_id"]

    breakpoint()

    table_service.delete_entity(LISTS, list_id, "list")
    for item in table_service.query_entities(ITEMS, filter=f"PartitionKey eq '{list_id}'"):
        table_service.delete_entity(ITEMS, item.PartitionKey, item.RowKey)

    return web.HTTPOk()


@routes.get("/lists/{list_id}/{row_key}")
async def get_item(request):
    table_service = request.app["connection-string"]
    list_id = request.match_info["list_id"]
    row_key = request.match_info["row_key"]

    entity = table_service.get_entity(ITEMS, list_id, row_key)

    return web.json_response({"row_key": entity.RowKey, "text": entity.text, "done": entity.done})


@routes.put("/lists/{list_id}/{row_key}")
async def update_item(request):
    table_service = request.app["connection-string"]
    list_id = request.match_info["list_id"]
    row_key = request.match_info["row_key"]
    body = await request.json()

    item = Entity()
    item.PartitionKey = list_id
    item.RowKey = row_key
    item.text = body["text"]
    item.done = body["done"]

    table_service.update_entity(ITEMS, item)

    return web.HTTPOk()


@routes.delete("/lists/{list_id}/{row_key}")
async def delete_item(request):
    table_service = request.app["connection-string"]
    list_id = request.match_info["list_id"]
    row_key = request.match_info["row_key"]

    try:
        table_service.delete_entity(ITEMS, list_id, row_key)
    except AzureMissingResourceHttpError:
        return web.HTTPNotFound()

    return web.HTTPOk()
