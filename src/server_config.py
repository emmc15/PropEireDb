"""
Sets the config for the application
"""
# Flask modules
import os

import dash
import dash_bootstrap_components as dbc
from flask import Flask
from flask_caching import Cache

from dotenv import load_dotenv
from utils.db_connections import (
    create_postgres_sql_connection,
    create_redis_connection,
    create_sql_alchemy_engine,
)  # pylint: disable=import-error


# Global Settings
load_dotenv()
PG_CONNECTION = create_postgres_sql_connection(os.getenv("POSTGRES_DSN"))
PG_ALCHEMY_CONNECTION = create_sql_alchemy_engine(os.getenv("POSTGRES_DSN"))
REDIS_CONNECTION = create_redis_connection(os.getenv("REDIS_DSN"))
REDIS_TIMEOUT = 60

server = Flask(__name__)  # NOTE: https://community.plot.ly/t/how-to-run-dash-on-a-public-ip/4796/3


application = dash.Dash(
    name="app1",
    server=server,
    external_stylesheets=[dbc.themes.FLATLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

CACHE = Cache(
    application.server,
    config={
        # try 'filesystem' if you don't want to setup redis
        "CACHE_TYPE": "redis",
        "CACHE_REDIS_URL": os.getenv("REDIS_DSN"),
    },
)

if __name__ == "__main__":
    pass
