"""

"""
from datetime import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd
from sqlalchemy.engine import Engine

from models.input_model import InputModel
import typing
from sqlalchemy import text


class DataModel(object):
    """
    Object Generates the data for various graphs by a dictionary input
    """

    def __init__(self, input_parser: InputModel, db_engine: Engine):
        """
        Takes in the cleansed input from the input model as to generate the data
        """

        self.input_parser = input_parser
        self.engine = db_engine

    def import_json(self, json_input: typing.Dict[str, typing.Any]) -> None:
        """
        Abstracting input to create object outside of functions
        """
        # Takes the raw inputs and converts to a cleansed format
        cleansed_json_input = self.input_parser.cleanse_input(json_input)

        # Assigns where the data is coming from when it's a main table
        if cleansed_json_input["region"] == "dublin_region":
            self.main_data_table = "propeiredb.residential_register_dublin_mapped"
        else:
            self.main_data_table = "propeiredb.residential_register"

        # Assigns the column of interest for the grouped data
        if cleansed_json_input["region"] == "dublin_region":
            self.grouping_column = "region"
        else:
            self.grouping_column = cleansed_json_input["region"].lower()

        # Creates the query style string for selecting the areas
        self.area_choices = ", ".join(f"'{i}'" for i in cleansed_json_input["area"])

        # Dates
        self.start_date = cleansed_json_input["start_date"]
        self.end_date = cleansed_json_input["end_date"]

        # Generate periods
        current_date = datetime.strptime(cleansed_json_input["start_date"], "%Y-%m-%d")
        max_date = datetime.strptime(cleansed_json_input["end_date"], "%Y-%m-%d")
        periods = []
        while current_date <= max_date:
            periods.append(current_date.strftime("%Y-%m"))
            current_date += relativedelta(months=1)

        self.period_choices = ", ".join(f"'{i}'" for i in periods)

        # Assigns the key to the cache
        params = [self.main_data_table, self.grouping_column, self.area_choices, self.start_date, self.end_date]

        self.joined_params = ":".join(params)

    def total_query(self, agg_func: typing.AnyStr) -> float:
        """
        creates a sql query with an aggregated function of a single value selected from all choices in region based on periods selected

        Args:
            agg_func(typing.AnyStr): sum, avg, count

        Returns:
            float: _description_
        """
        inner_query = f"""
        SELECT
            {agg_func}(price)
        from {self.main_data_table}
        where sale_date between '{self.start_date}' 
        and '{self.end_date}' 
        and {self.grouping_column} in ({self.area_choices});
        """

        return float(pd.read_sql(text(inner_query), con=self.engine.connect())[agg_func])

    def pull_choices_grouped_by_year(self) -> pd.DataFrame:
        """
        For use with the bar chart option to group by year. This gives a total value for region choices by year on aggregate


        Data is pulled from the aggregated table using imported json input:
            regions = (Province, County, Dublin Area)
            Choice = corresponding areas in regions
            years = years selected
            periods = periods select
            agg = boolean, for checking if to return aggregated views or full data table


        Returns:
            pd.DataFrame()
        """
        data_source = "propeiredb.{}_agg_data".format(self.grouping_column)
        query = f"""
            SELECT
                {self.grouping_column},
                year,
                round(sum(total_value),2) as total_value,
                round(avg(avg_price),2) as avg_price,
                round(sum(num_of_sales),2) as num_of_sales
                FROM {data_source}
                WHERE period in ({self.period_choices})
                and {self.grouping_column} in ({self.area_choices}) group by {self.grouping_column}, year;"""

        # print(f"pulled_group_choices_by_year: {query}")
        return pd.read_sql(text(query), con=self.engine.connect())

    def pull_data_query(self) -> pd.DataFrame:
        """
        creates a sql query and pulls data from the database into dataframe

        Parameters:
        -----------
            regions = (Province, County, Dublin Area)
            Choice = corresponding areas in regions
            years = years selected
            periods = periods select

        Returns:
            pd.DataFrame: _description_
        """

        query = f"SELECT * FROM {self.main_data_table} WHERE sale_date between '{self.start_date}' and '{self.end_date}' and {self.grouping_column} in ({self.area_choices});"

        return pd.read_sql(text(query), con=self.engine.connect()).sort_values(by="period")

    def pull_grouped_data(self, grouping=None) -> pd.DataFrame:
        """
        creates the full group by for feeding into a few of the series chart

        Args:
            grouping (_type_, optional): _description_. Defaults to None.

        Returns:
            pd.DataFrame: _description_
        """

        data_source = "propeiredb.{}_agg_data".format(self.grouping_column)

        sub_query = f"select * from {data_source} where period in ({self.period_choices}) and {self.grouping_column} in ({self.area_choices})"
        # sub_query=sub_query.format(data_source, periods, column, choice)

        if grouping == None:
            query = f"SELECT {self.grouping_column}, round(sum(total_value),2) as total_value, round(avg(avg_price),2) as avg_price, round(sum(num_of_sales),2) as num_of_sales from ({sub_query}) as sub group by {self.grouping_column}"

        else:
            query = f"SELECT {grouping}, {self.grouping_column},round(sum(total_value),2) as total_value, round(avg(avg_price),2) as avg_price, round(sum(num_of_sales),2) as num_of_sales from ({sub_query}) as sub group by {grouping}, {self.grouping_column} order by {grouping}"

        # print(f"pulled_grouped_data: {query}")
        return pd.read_sql(text(query), con=self.engine.connect())

    def market_share_per_area(self):
        """
        gives a list of all the market share based on region, choices, and year-periods
        NOTE: This is relative market share


        Parameters:
        -----------
            regions = (Province, County, Dublin Area)
            Choice = corresponding areas in regions
            years = years selected
            periods = periods select


        Returns:
            pd.DataFrame: list of market share by area for the selection periods
            columns=['total_value', region_column, 'avg_price','market_share', 'num_of_sales']

        """
        # Total value of the region selected over the selected period
        data = self.pull_grouped_data()

        # Total value of the choices made
        total_value = data["total_value"].sum()

        data["market_share"] = data["total_value"].apply(lambda x: round((x / total_value) * 100, 3))
        return data

    def market_share_selected(self):
        """
        Gives a df of market share selected for period and all market share for period
        NOTE: This non relative market share for a given period
        Returns:
        --------
            pd.DataFrame(), two columns(total_value and market share and choice) two rows(selected regions, total)
        """

        # Total value of all areas for the period
        total_value = f"SELECT sum(total_value) as total_value from propeiredb.{self.grouping_column}_agg_data WHERE period in ({self.period_choices}) and {self.grouping_column} is not null"
        total_value = float(pd.read_sql(text(total_value), con=self.engine.connect())["total_value"])

        # pulls in the total select value
        data = self.pull_grouped_data()
        data = float(data["total_value"].sum())

        selected_market_share = (data / total_value) * 100
        total_market_share = ((total_value - data) / total_value) * 100
        frame = {
            "choice": ["Selected", "Remaining"],
            "total_value": [data, total_value],
            "market_share": [selected_market_share, total_market_share],
        }

        return pd.DataFrame.from_dict(frame)


if __name__ == "__main__":
    pass
