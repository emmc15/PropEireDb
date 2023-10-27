"""
Functions to help with the geoencoding
"""
from typing import Any, Dict, List
import json
import os
import re
import logging
import toml

from shapely.geometry.polygon import Polygon
from shapely.geometry import Point
import pandas as pd
from elasticsearch import Elasticsearch, helpers

from .db_utils import recursive_list_float_extractor
from .pandas_upsert import PandaSqlPlus
from .db_connections import create_postgres_sql_connection, create_sql_alchemy_engine
from .geojson_map_cleanse import DUBLIN_GEOJSON


# -----------------------------------------------------------------------------
# ElasticSearch Utils
# -----------------------------------------------------------------------------


def upload_df_to_elasticsearch(df: pd.DataFrame, es: Elasticsearch, wipe_data: bool = False):
    """
    _summary_

    Args:
        df (pd.DataFrame): _description_
        es (Elasticsearch): _description_
        wipe_data (bool, optional): _description_. Defaults to False.
    """

    df_dict = df.to_dict("records")
    index = "propeiredb_geo_encode"

    # Wipes and inserts back all the data
    if wipe_data is True:
        try:
            es.delete_by_query(index=index, body={"query": {"match_all": {}}})
            es.indices.create(index=index, ignore=400)
        except Exception as e:
            logging.warning(e)

    helpers.bulk(es, df_dict, index=index)


def query_mapped_data(query: str, doc_attr: str, es: Elasticsearch, **kwargs) -> List[str]:
    """
    _summary_

    Args:
        query (str): _description_
        doc_attr (str): _description_
        es (Elasticsearch): _description_

    Returns:
        List[str]: _description_
    """

    query_body = {"query": {"match": {doc_attr: query}}}

    data = es.search(index="propeiredb_geo_encode", body=query_body)
    base_struct = data["hits"]["hits"]
    if len(base_struct) >= 1:
        max_hit = base_struct[0]["_source"]
        for keys, values in kwargs.items():
            max_hit[keys] = values

        return max_hit
    return None


# -----------------------------------------------------------------------------
# Geo Encoding Functions
# -----------------------------------------------------------------------------


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


def assign_region(lon, lat, geojson: Dict[str, Polygon]):
    """
    Assigns a region based on the lat and lon coordinates and the geojson_details variable defined elsewhere


    Paramaters:
    -----------
        lat=float(), latitude point
        lon=float(), longitude point
        file=dict(), expects a dicitonary of {'arb_key_pair': {'shape': points}}

    Returns:
    --------
        str(), the assignement key from the geojson file
    """

    point = Point(lon, lat)

    for region_name, polygon in geojson.items():
        if polygon.contains(point):
            return region_name

    return None


def backfill_geo_encode_data(max_date_filter: str = "2019-12-31") -> None:
    """
    Runs a backfill by mapping the address through elastic search
    """
    state = os.getenv("state")
    this_folder_path = os.path.dirname(os.path.abspath(__file__))
    root_folder_path = "/".join(this_folder_path.split("/")[:-2])  # pylint: disable=invalid-name
    data_folder_path = os.path.join(root_folder_path, "data", "GeoJSON")
    toml_file_path = os.path.join(root_folder_path, "src", f"{state}.toml")

    # Folder paths
    db_connection = create_sql_alchemy_engine(toml_file_path, header="postgres")
    pg_connection = create_postgres_sql_connection(toml_file_path, header="postgres")

    # Database Util Object
    postgres_pandas = PandaSqlPlus(pg_connection)
    es_header = toml.load(toml_file_path)["elasticsearch"]
    ES = Elasticsearch([{"host": es_header["host"], "port": es_header["port"]}])

    # pull unmapped data
    query = f"SELECT * FROM propeiredb.residential_register_dublin_unmapped where sale_date <= '{max_date_filter}'"
    unmapped_data = pd.read_sql(query, con=db_connection)

    # Create Polygon from geojson data to map lat lon to region
    DUBLIN_POLY_DICT = generate_region_points(DUBLIN_GEOJSON)

    # Readin all json documents
    interested_file_name = "encoded_dublin"
    interested_files = os.listdir(data_folder_path)
    interested_files = list(filter(lambda x: x if interested_file_name in x else None, interested_files))
    all_encoded_data = []
    for i in interested_files:
        json_data = json.load(open(os.path.join(data_folder_path, i), "r"))
        for index, value in json_data.items():
            temp_dict = {}
            if len(value) == 0:
                continue
            extracted_dict = value[0]

            # Skip if its a bad address
            if len(extracted_dict["formatted_address"].split(" ")) == 1:
                continue

            cleansed_address = re.sub(r"(\d+), ", "", extracted_dict["formatted_address"])
            temp_dict["formatted_address"] = cleansed_address.lower()
            temp_dict["lat"] = extracted_dict["geometry"].get("location").get("lat")
            temp_dict["lon"] = extracted_dict["geometry"].get("location").get("lng")

            all_encoded_data.append(temp_dict)

    # Clean frame and map the regions
    all_encoded_data = pd.DataFrame(all_encoded_data).drop_duplicates()
    all_encoded_data["region"] = all_encoded_data.apply(
        lambda x: assign_region(x["lon"], x["lat"], DUBLIN_POLY_DICT), axis=1
    )
    all_encoded_data.dropna(inplace=True)
    upload_df_to_elasticsearch(all_encoded_data, ES, wipe_data=True)

    # Run the unmapped data against the mapped data to enrich the database
    unmapped_data = unmapped_data.to_dict("records")
    list_of_results = []
    for row in unmapped_data:
        results = query_mapped_data(
            row["address"], "formatted_address", ES, address=row["address"], address_hash=row["address_hash"]
        )
        if results is not None:
            logging.info(f"mapped {row['address']} to {results['formatted_address']}")
            list_of_results.append(results)

    mapped_data = pd.DataFrame(list_of_results)
    columns_to_rename = {
        "address_hash": "address_hash",
        "address": "input_address",
        "formatted_address": "output_address",
        "lat": "lat",
        "lon": "lon",
        "region": "region",
    }
    mapped_data.rename(columns=columns_to_rename, inplace=True)
    mapped_data = mapped_data[columns_to_rename.values()]
    logging.info("upserting mapped data to the database")
    postgres_pandas.upsert_dataframe(mapped_data, "propeiredb", "geo_encoding_lookup")


if __name__ == "__main__":
    pass
