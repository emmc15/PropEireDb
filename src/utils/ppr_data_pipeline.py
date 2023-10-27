"""
Downloads and extracts the data from the property price register .ie
"""
from datetime import datetime
from hashlib import md5
import logging
import os
from typing import Union
import re
import zipfile

import requests
import pandas as pd
from numpy import nan as NaN
from psycopg2.extensions import connection as PostgresConnection

from .pandas_upsert import PandaSqlPlus

# -----------------------------------------------------------------------------
# Extraction
# -----------------------------------------------------------------------------

# Examples for year can be "ALL", "2021", "2019" or for months as well "2018-01" where 01 is january
PPR_RESIDENTIAL_DATA_URL = (
    "https://propertypriceregister.ie/website/npsra/ppr/npsra-ppr.nsf/Downloads/PPR-{filter}.zip/$FILE/PPR-{filter}.zip"
)
PPR_COMMERCIAL_DATA_URL = "https://propertypriceregister.ie/website/npsra/ppr/npsra-ppr-com.nsf/Downloads/CLR-{filter}.csv/$FILE/CLR-{filter}.csv"


def download_property_data(
    data_path: str = "/tmp", ppr_filter: str = "ALL", property_type: str = "residential"
) -> bool:
    """
    Downloads property from the propertypriceregister.ie website

    Args:
        ppr_filter (str, optional): Examples for year can be "ALL", "2021", "2019" or for months as well "2018-01" where 01 is january.
            Defaults to "ALL".
        property_type (str, optional): Must be residential or commercial. Defaults to 'residential'.
        data_path (str, optional): Folder where the file will be downloaded. Defaults to "/tmp".

    Returns:
        bool: True if downloaded, returns False if couldn't be downloaded
    """
    assert os.path.exists(data_path), "Can not download data to a path that does not exist"
    assert property_type in (
        "residential",
        "commercial",
    ), f"property_type is expected to be 'residential' or 'commercial', instead recieved {property_type}"

    file_type = ".csv"
    if ppr_filter == "ALL":
        file_type = ".zip"

    if property_type == "residential":
        download_url = PPR_RESIDENTIAL_DATA_URL
    elif property_type == "commercial":
        download_url = PPR_COMMERCIAL_DATA_URL
    else:
        raise ValueError("Did not recieve the correct valu")

    download_name = "".join([property_type, "-", ppr_filter, file_type])
    logging.info(f"Downloading {download_name}")
    logging.info(download_url.format(filter=ppr_filter))
    try:
        download_to_mem = requests.get(download_url.format(filter=ppr_filter), verify=False)
    except Exception as e:
        logging.exception(e)
        logging.warning(f"could not download from URL {download_url.format(filter=ppr_filter)}")
        return False
    with open(os.path.join(data_path, download_name), "wb") as f:
        f.write(download_to_mem.content)

    if file_type == ".zip":
        logging.info(f"unzipping {download_name}")
        with zipfile.ZipFile(os.path.join(data_path, download_name), "r") as zip_ref:
            zip_file_names = zip_ref.namelist()
            zip_ref.extractall(data_path)

        if "PPR-ALL.csv" in zip_file_names:
            download_name = download_name.replace(".zip", ".csv")
            logging.info(f"Renaming PPR-ALL.csv to {download_name}")
            os.rename(
                os.path.join(data_path, "PPR-ALL.csv"),
                os.path.join(data_path, download_name),
            )
            os.remove(os.path.join(data_path, download_name.replace(".csv", ".zip")))

    return True


# -----------------------------------------------------------------------------
# Transformations
# -----------------------------------------------------------------------------


def province_assignment(county: str) -> str:
    """
    _summary_

    Args:
        county (str): _description_

    Returns:
        str: _description_
    """

    # Provinces
    connacht = ["Galway", "Leitrim", "Mayo", "Roscommon", "Sligo"]
    munster = ["Limerick", "Tipperary", "Clare", "Kerry", "Cork", "Waterford"]

    leinster = [
        "Carlow",
        "Dublin",
        "Kildare",
        "Kilkenny",
        "Laois",
        "Longford",
        "Louth",
        "Meath",
        "Offaly",
        "Westmeath",
        "Wexford",
        "Wicklow",
    ]

    ulster = [
        "Antrim",
        "Armagh",
        "Cavan",
        "Donegal",
        "Down",
        "Fermanagh",
        "Londonderry",
        "Monaghan",
        "Tyrone",
    ]
    county = county.capitalize()

    if county in connacht:
        return "Connacht"
    elif county in munster:
        return "Munster"
    elif county in leinster:
        return "Leinster"
    elif county in ulster:
        return "Ulster"
    else:
        return None


def pull_number(input_text: str) -> Union[str, None]:
    """
    Function using regex to extract only number from input, meant to be used on pandas df with apply
    """

    if isinstance(input_text, str):

        t = re.search(r"\d+", input_text)
        if t is not None:
            return t.group(0)
        else:
            return input_text
    else:
        return None


def process_downloaded_data(ppr_file_path: str) -> pd.DataFrame:
    """
    _summary_

    Args:
        ppr_file_path (str): _description_

    Returns:
        pd.DataFrame: _description_
    """

    assert os.path.isfile(ppr_file_path), f"{ppr_file_path} is a not a file path or does not exist"

    new_data = pd.read_csv(ppr_file_path, encoding="ISO-8859-1")

    columns = [
        "sale_date",
        "address",
        "county",
        "postal_code",
        "price",
        "not_full_market_price",
        "vat_exclusive",
        "property_description",
        "property_size_description",
    ]

    new_data.columns = columns


    # Annoymous function ran through apply to clean up the price to cast as numeric
    new_data["price"] = new_data["price"].apply(lambda x: x.strip("\x80").replace(",", "").lower())

    new_data["price"] = pd.to_numeric(new_data["price"])

    # clean and change the data type of the pandas dataframe for date for sale
    new_data["sale_date"] = new_data["sale_date"].apply(
        lambda x: datetime.strptime(x.replace("/", "-"), "%d-%M-%Y").strftime("%Y-%M-%d")
    )

    new_data["sale_date"] = pd.to_datetime(new_data["sale_date"])
    new_data["year"] = new_data["sale_date"].apply(lambda x: x.strftime("%Y"))

    new_data["month"] = new_data["sale_date"].apply(lambda x: x.strftime("%m"))

    new_data["period"] = new_data["sale_date"].apply(lambda x: (x.strftime("%Y-%m")))

    new_data["sale_date"] = new_data["sale_date"].apply(lambda x: x.date())

    # lowercase and standerise addresses for joining
    new_data["address"] = new_data["address"].apply(
        lambda x: x.replace("\\", "").replace("*", "8").lower()  # flatten, typo from ppr, and escape character typo
    )

    # Ensure the values are sorted correctly
    new_data = new_data.sort_values("sale_date")

    new_data["province"] = new_data["county"].apply(province_assignment)
    new_data["dublin_area_code"] = new_data["postal_code"].apply(pull_number)

    # Create unique identifier
    new_data["address_hash"] = new_data["address"].apply(lambda x: md5(x.encode()).hexdigest())

    # Replace None with with NaN
    new_data = new_data.fillna(value=NaN)

    return new_data


def process_mapped_data(encoded_df: pd.DataFrame) -> pd.DataFrame:
    """
    _summary_

    Args:
        encoded_df (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: _description_
    """
    columns_to_keep = ["input_address", "output_address", "lat", "lon"]
    encoded_df = encoded_df[columns_to_keep]

    encoded_df["input_address"] = encoded_df["input_address"].apply(lambda x: x.lower())
    encoded_df["address_hash"] = encoded_df["input_address"].apply(lambda x: md5(x.encode()).hexdigest())
    encoded_df = encoded_df.dropna()

    return encoded_df


# -----------------------------------------------------------------------------
# Load
# -----------------------------------------------------------------------------


def upload_ppr_df(ppr_df: pd.DataFrame, table_name: str, pg_connection: PostgresConnection) -> None:
    """
    _summary_

    Args:
        ppr_df (pd.DataFrame): _description_
        table_name (str): _description_
        pg_connection (PostgresConnection, optional): _description_. Defaults to PG_CONNECTION.
    """

    uploader = PandaSqlPlus(pg_connection, threads=12)

    uploader.upsert_dataframe(ppr_df, "propeiredb", table_name)

    return None


if __name__ == "__main__":
    pass
