"""
Functions to help with the geoencoding
"""
from typing import Any, Dict
import dataclasses
import googlemaps
import logging

import pandas as pd
from psycopg2.extensions import connection as PostgresConnection
from shapely.geometry.polygon import Polygon
from shapely.geometry import Point




from .db_utils import recursive_list_float_extractor
from .pandas_upsert import PandaSqlPlus
from .db_connections import create_postgres_sql_connection, create_sql_alchemy_engine
from .geojson_map_cleanse import DUBLIN_GEOJSON


# -----------------------------------------------------------------------------
# Geo Encoding Functions
# -----------------------------------------------------------------------------
@dataclasses.dataclass
class GeoEncodedAddress():
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


def assign_region(lon, lat, geojson: Dict[str, Polygon]) -> str | None:
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

def get_addresses_to_encode(postgres_engine) -> pd.DataFrame:
    """
    Extracts the addresses from the database that have not been geoencoded

    Args:
        postgres_engine (_type_): _description_

    Returns:
        pd.DataFrame: _description_
    """
    with postgres_engine.connect() as conn:
        query = """
        SELECT * FROM propeiredb.missing_geo_encoded_addresses
        """
        df = pd.read_sql(query, conn)

    return df



if __name__ == "__main__":
    pass
