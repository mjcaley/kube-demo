import argparse
import logging
import os

from aiohttp import web
from azure.cosmosdb.table.tableservice import TableService

from .endpoints import *


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--connection-string", default=os.environ.get("API_CONNECTION_STRING"))
    args = parser.parse_args()
    table_service = TableService(connection_string=args.connection_string)

    initialize_db(table_service)
    app = web.Application()
    app.add_routes(routes)
    app['connection-string'] = table_service

    web.run_app(app, port=8080)
