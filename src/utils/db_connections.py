"""
Returns the Database Connections Objects as defined in the .config.ini
"""
import logging

from redis import StrictRedis
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from psycopg2 import connect as pg_connection
from psycopg2.extensions import connection as PostgresConnection


# from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT # <-- ADD THIS LINE
log = logging.getLogger(__name__)


def create_sql_alchemy_engine(dsn: str) -> Engine:
    """
    [summary]

    Args:
        path_to_config (str, optional): [description]. Defaults to '.config.ini'.
        header (str, optional): [description]. Defaults to 'postgres'.

    Returns:
        Engine: [description]
    """
    # Read in config Connection
    postgres_engine = create_engine(dsn)

    return postgres_engine


def create_postgres_sql_connection(dsn: str) -> PostgresConnection:
    """
    [summary]

    Args:
        path_to_config (str): [description]
        header (str, optional): [description]. Defaults to 'postgres'.

    Returns:
        engine: [description]
    """
    postgres_connection = pg_connection(dsn)
    # postgres_connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # <-- ADD THIS LINE
    postgres_connection.autocommit = True
    return postgres_connection


def create_redis_connection(dsn: str) -> StrictRedis:
    """
    [summary]

    Args:
        path_to_config (str): [description]
        header (str, optional): [description]. Defaults to 'redis'.

    Returns:
        Redis: [description]
    """
    # Read in config Connection

    redis_connection = StrictRedis(dsn)
    return redis_connection
