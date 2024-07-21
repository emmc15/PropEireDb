"""
click script to allow some maintenace with in docker container
"""
import logging
import os

import click
from dotenv import load_dotenv
import googlemaps

from utils import db_connections as db_con
from utils.ppr_data_pipeline import download_property_data, process_downloaded_data, upload_ppr_df
from utils.geo_encode_data import encode_and_upload_missing_addresses

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)


load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_KEY")

# -----------------------------------------------------------------------------
# Prep
# -----------------------------------------------------------------------------


@click.group()
def propeiredb_cli():
    """
    Collection of comman commands to execute for running the propeiredb site
    """
    pass

# -----------------------------------------------------------------------------
# Extract data from PPR
# -----------------------------------------------------------------------------


@propeiredb_cli.command()
@click.option("--property-type", default="residential")
@click.option("--period", default="ALL")
@click.option("--force-build", default=False)
def run_pipeline(property_type: str, period: str, force_build: bool = False) -> None:
    """
    Upserts data into postgres database

    Args:
        property_type (str): _description_
        period (str): _description_
    """
    this_folder_path = os.path.dirname(os.path.abspath(__file__))
    root_folder_path = "/".join(this_folder_path.split("/")[:-1])  # pylint: disable=invalid-name
    data_folder_path = os.path.join(root_folder_path, "data", "raw_data")
    file_name = f"{property_type}-{period}.csv"
    file_path = os.path.join(data_folder_path, file_name)

    if os.path.exists(data_folder_path) is False:
        os.mkdir(data_folder_path)

    downloaded = True
    if os.path.exists(file_path) is False or force_build is True:
        downloaded = download_property_data(data_folder_path, period, property_type)

    if downloaded is False and os.path.exists(file_name) is False:
        logging.warning("could not parse file as downloading failed")
        return None


    df = process_downloaded_data(file_path)

    db_connection = db_con.create_postgres_sql_connection(os.getenv("POSTGRES_DSN"))

    upload_ppr_df(df, "residential_register", db_connection)


# -----------------------------------------------------------------------------
# Backfill Previously mapped data to geo_encode_lookup table
# -----------------------------------------------------------------------------

@propeiredb_cli.command()
@click.option("--batch-size", default=100)
def geoencode_missing_addresses(batch_size: int) -> None:
    """
    Backfills the geo_encode_lookup table with previously mapped data
    """
    db_connection = db_con.create_postgres_sql_connection(POSTGRES_DSN)
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

    encode_and_upload_missing_addresses(db_connection, gmaps, batch_size=batch_size)


if __name__ == "__main__":
    load_dotenv()
    propeiredb_cli()
