"""
Functions to help with the geoencoding
"""
from typing import Any, Dict, List
import dataclasses
import googlemaps
import logging

import pandas as pd
from psycopg2.extensions import connection as PostgresConnection
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point

from .db_utils import recursive_list_float_extractor
from .pandas_upsert import PandaSqlPlus
from .geojson_map_cleanse import DUBLIN_GEOJSON


# -----------------------------------------------------------------------------
# Geo Encoding Functions
# -----------------------------------------------------------------------------
@dataclasses.dataclass
class GeoEncodedAddress:
    input_address: str
    output_address: str
    lat: float
    lon: float
    address_hash: str | None = None
    region: str | None = None


def encode_address(address: str, client: googlemaps.Client) -> GeoEncodedAddress:
    geocode_result = client.geocode(address)

    if len(geocode_result) == 0:
        raise ValueError("No results found")
    geocode_result = geocode_result[0]

    output_address = geocode_result["formatted_address"]
    lat = geocode_result["geometry"]["location"]["lat"]
    lon = geocode_result["geometry"]["location"]["lng"]

    return GeoEncodedAddress(input_address=address, output_address=output_address, lat=lat, lon=lon)


def generate_region_points(geojson: Dict[str, Any]) -> Dict[str, Polygon]:
    """
    Given a converted geojson, it extracts the feature ID's and returns a dict of polygon points

    Args:
        geojson (Dict[str, Any]): _description_

    Returns:
        Dict[str, Polygon]: _description_
    """
    geojson = geojson["features"]
    mapped_polygons = {}
    for i in geojson:
        #  Returns list of lists which each contain the lat and lon points which is used in polygon object
        points = recursive_list_float_extractor(i["geometry"]["coordinates"])
        #  Creates the polygon object from data file
        poly = Polygon(points)
        mapped_polygons[i["id"]] = poly

    return mapped_polygons


def assign_region(lon: float, lat: float, geojson: Dict[str, Polygon]) -> str | None:
    """
    Assigns a region based on the lat and lon coordinates and the geojson_details variable defined elsewhere

    Args:
        lon (_type_): _description_
        lat (_type_): _description_
        geojson (Dict[str, Polygon]): _description_

    Returns:
        str | None: the assignement key from the geojson file
    """

    point = Point(lon, lat)

    for region_name, polygon in geojson.items():
        if polygon.contains(point):
            return region_name

    return None


# -----------------------------------------------------------------------------
# Data Extraction
# -----------------------------------------------------------------------------


def get_addresses_to_encode(postgres_engine: PostgresConnection, batch_size: int = 100) -> pd.DataFrame:
    """
    Extracts the addresses from the database that have not been geoencoded

    Args:
        postgres_engine (_type_): _description_

    Returns:
        pd.DataFrame: _description_
    """
    assert isinstance(batch_size, int), "Batch size must be an integer"
    assert batch_size > 0, "Batch size must be greater than 0"

    with postgres_engine as conn:
        query = f"""
        SELECT * FROM propeiredb.missing_geo_encoded_addresses LIMIT {batch_size};
        """
        df = pd.read_sql(query, conn)

    return df


# -----------------------------------------------------------------------------
# Transformation
# -----------------------------------------------------------------------------


def get_encoded_addresses(
    df: pd.DataFrame, client: googlemaps.Client, region: Dict[str, Polygon]
) -> List[GeoEncodedAddress]:
    """
    Takes addressses from the dataframe and encodes them using the googlemaps client
    Returns a list of GeoEncodedAddress objects
    """
    assert "address" in df.columns, "Address column not found in dataframe"

    df = df.to_dict(orient="records")
    encoded_addresses = []
    for i in df:
        target_address = i["address"]

        if "ireland" not in target_address.lower():
            target_address += ", Ireland"

        geo_encoded_address = encode_address(target_address, client)
        geo_encoded_address.input_address = i["address"]
        geo_encoded_address.address_hash = i["address_hash"]
        geo_encoded_address.region = assign_region(geo_encoded_address.lon, geo_encoded_address.lat, region)
        encoded_addresses.append(geo_encoded_address)

    return encoded_addresses


# -----------------------------------------------------------------------------
# Upload
# -----------------------------------------------------------------------------


def encode_and_upload_missing_addresses(
    postgres_engine: PostgresConnection,
    client: googlemaps.Client,
    region: Dict[str, Polygon] = generate_region_points(DUBLIN_GEOJSON),
    batch_size: int = 40_000,
    schema_name: str = "propeiredb",
    table_name: str = "geo_encoding_lookup",
) -> None:
    """
    Encodes and uploads missing addresses to the database
    """
    logging.info("Starting to encode and upload missing addresses")
    df = get_addresses_to_encode(postgres_engine, batch_size)
    logging.info(f"Extracted {len(df)} addresses to encode")
    encoded_addresses = get_encoded_addresses(df, client, region)
    logging.info(f"Encoded {len(encoded_addresses)} addresses")
    encoded_addresses = pd.DataFrame(encoded_addresses)

    with postgres_engine as conn:
        upsert = PandaSqlPlus(conn)
        upsert.upsert_dataframe(df=encoded_addresses, schema_name=schema_name, table_name=table_name, update_rows=True)

    logging.info(f"Uploaded {len(encoded_addresses)} addresses to the database")


if __name__ == "__main__":
    pass
