"""
    @about: Generates clean geojson files
"""
import json
import os
from typing import Dict


# ----------------------------------------------------------------------
# Cleans up Dublin geojson
# ----------------------------------------------------------------------
def cleanse_dublin_geojson(geofile: str) -> Dict:
    """
    _summary_

    Args:
        geofile (str): _description_

    Returns:
        Dict: _description_
    """
    assert os.path.exists(geofile), f"{geofile} is not a path that exists"

    # importing dublin geojson
    with open(geofile, encoding="utf-8") as geofile_json:
        dublin_geojson = json.load(geofile_json)

    # Fixes up the details
    number_of_features = 0
    while number_of_features < len(dublin_geojson["features"]):
        dublin_name = str(dublin_geojson["features"][number_of_features]["properties"]["id"])
        if dublin_name == "0":
            dublin_name = "Phoenix Park"
        elif dublin_name == "61":
            dublin_name = "6w"
        elif dublin_name == "66":
            dublin_name = "D12"
        elif dublin_name == "100":
            dublin_name = "Dun Laoghaire/Rathdown"
        else:
            dublin_name = f"D{dublin_name}"
        dublin_geojson["features"][number_of_features]["properties"]["id"] = dublin_name
        dublin_geojson["features"][number_of_features]["id"] = dublin_name
        number_of_features = number_of_features + 1

    return dublin_geojson


# ----------------------------------------------------------------------
# Cleans up County
# ----------------------------------------------------------------------
def cleanse_county_geojson(geofile: str) -> Dict:
    """
    _summary_

    Args:
        geofile (str): _description_

    Returns:
        Dict: _description_
    """
    # Importing county geojson
    with open(geofile, encoding="utf-8") as geofile:
        county_geojson = json.load(geofile)

    # Removes the First instance of the the cork geojson
    county_geojson["features"].pop(0)

    # Edits the county_geojson to standardize names
    for i in range(0, len(county_geojson["features"])):
        name = county_geojson["features"][i]["properties"]["FIRST_COUNTY"]
        county_geojson["features"][i]["properties"]["id"] = name.title().strip(" ")
        county_geojson["features"][i]["id"] = name.title().strip(" ")

    return county_geojson


# ----------------------------------------------------------------------
# Cleans up Province
# ----------------------------------------------------------------------
def cleanse_province_geojson(geofile: str) -> Dict:
    """
    _summary_

    Args:
        geofile (str): _description_

    Returns:
        Dict: _description_
    """
    # Importing provincal areas
    with open(geofile, encoding="utf-8") as province_geofile:
        province_geojson = json.load(province_geofile)

    # Edits the county_geojson to standardize names
    for i in range(0, len(province_geojson["features"])):
        name = province_geojson["features"][i]["properties"]["PROVINCE"]
        province_geojson["features"][i]["properties"]["id"] = name.title().strip(" ")
        province_geojson["features"][i]["id"] = name.title().strip(" ")

    return province_geojson


# -----------------------------------------------------------------------------
# Global Variables
# -----------------------------------------------------------------------------
base_directory = "/".join(list(os.path.dirname(os.path.abspath(__file__)).split("/")[0:-1]))
dublin_geojson_path = os.path.join(base_directory, "assets/dublin_boundaries.json")
province_geojson_path = os.path.join(base_directory, "assets/province_boundaries.json")
county_geojson_path = os.path.join(base_directory, "assets/county_boundaries.json")

DUBLIN_GEOJSON = cleanse_dublin_geojson(dublin_geojson_path)
PROVINCE_GEOJSON = cleanse_province_geojson(province_geojson_path)
COUNTY_GEOJSON = cleanse_county_geojson(county_geojson_path)


if __name__ == "__main__":
    pass
