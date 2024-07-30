import functools

import pandas as pd
import typing
from sqlalchemy import text


class InputModel(object):
    """
    Cleanses the input from the user to a more queryable format for feeding into the data model
    """

    def __init__(self, db_engine):
        # Pulls in the area options
        self._area_options = self._pull_area_options(db_engine)
        self._year_options = [str(i) for i in range(2010, 2020)]

    def cleanse_input(self, json_input: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """
        Takes in the json input from the property dashboard site under a hidden div.
        This is then converted to more workable interace for pulling from the database and graphs


        Args:
            json_input (typing.Dict[str, typing.Any]):key values found 'cached-inputs' div and call back in callbacks and layout

        Returns:
            typing.Dict[str, typing.Any]: with the same key values bar the invert with more queryable data format for inputs
        """
        # Sets the invert attribute
        try:
            self.invert = self._clean_invert(json_input["invert"])
        except NameError:
            self.invert = False

        # Dictionary to describe the cleansed model for generating the graphs
        cleansed_input = {}

        # Makes the column choice lower case for formatting into the next model
        if "Dublin" in json_input["region"].split(" "):
            cleansed_input["region"] = "dublin_region"
        else:
            cleansed_input["region"] = json_input["region"].lower()

        # cleans the regions up
        cleansed_input["area"] = self._clean_region_choices(json_input["area"], json_input["region"])

        # convert the dates
        cleansed_input["start_date"] = json_input["start_date"].split("T")[0]
        cleansed_input["end_date"] = json_input["end_date"].split("T")[0]

        return cleansed_input

    def _pull_area_options(self, engine):
        """
        Connencts to postgres database for pulling in the values

        Returns:
            dict(), key values of lists for province, county and encoded_region
        """
        area_options = {}
        columns = ["province", "county", "dublin_region"]
        for i in columns:
            if i != "dublin_region":
                # query to pull in all the needed columns
                query = f"SELECT {i} from propeiredb.residential_register where {i} is not null group by {i};"
                column_to_match = i
            else:
                column_to_match = "region"
                query = "SELECT region from propeiredb.residential_register_dublin_mapped where region is not null group by region;"

            # Pull the data from the db
            with engine.begin() as conn:
                data = pd.read_sql_query(sql=text(query), con=conn)

            data = list(data[column_to_match])
            area_options[i] = data
        return area_options

    def _clean_invert(self, invert: bool):
        """
        Returns the invert to a bool rather than list

        Args:
            invert (bool): _description_

        Returns:
            _type_: _description_
        """
        # Catches to see if invert to make choices inclusive or exclusive
        if isinstance(invert, list) and len(invert) == 1 and invert[0] is not None:
            # converts invert to bool if not already
            if isinstance(invert, list) and len(invert) >= 1:
                if True in invert:
                    invert = True
                else:
                    invert = False
        elif isinstance(invert, bool):
            return invert
        else:
            invert = False
        return invert

    def clean_list(self, value, list_of_values=None):
        """
        Cleans up inputs coming from inputs on the dashboard by ensuring and handling of 'All option

        Parameters:
        -----------
            value = list(), str() - the selection the user made
            list_of_values = list() - the pool of values the user could choice from

        Returns:
        --------
            list() of the correct values
        """
        # Checks if input was a string
        if isinstance(value, list) is False:
            if value == "All":
                return list_of_values
            # Expects a list for the output
            else:
                value = [value]

        # Variable to exclude invert seciton
        if "All" in list_of_values:
            list_of_values.pop(list_of_values.index("All"))

        # Removes all choice from the inputted values
        elif "All" in value:
            value.pop(value.index("All"))

        # Removes 'None' from the listings
        if None in value:
            value.pop(value.index(None))
        elif "None" in value:
            value.pop(value.index("None"))

        # Catches event of only all selected and popped
        if len(value) == 0:
            value = list_of_values

        # Checks whether to inver list
        if self.invert == True:
            # Uses set to get unique list and then separate via - and convert back to list
            value = list(set(list_of_values) - set(value))

        return value

    def _clean_month(self, month, year):
        """
        Given the year and time of year value, recreates month or list of months
        """
        # Cleans the month input
        output = []
        for i in year:
            for j in month:
                # for adding 0 to peirods below 10 for correct formatting
                if len(str(j)) == 1 and j != 9:
                    j = f"0{j+1}"
                else:
                    j = j + 1
                output.append(f"{i}-{j}")
        # Finds the minimum month
        output_min = functools.reduce(
            lambda x, agg: x if int(x.replace("-", "")) < int(agg.replace("-", "")) else agg, output
        )

        # Finds the max month
        output_max = functools.reduce(
            lambda x, agg: x if int(x.replace("-", "")) > int(agg.replace("-", "")) else agg, output
        )

        # create the range of months that were selected rather than
        # pull everything that would be inbetween the years and the first peirod and the last month
        # NOTE: above comment and below code was for old drop down input, kept in to keep flexibility in future and it works
        month_choices = []
        for i in range(int(year[0]), int(year[1]) + 1):
            for j in range(int(output_min[5:]), int(output_max[5:]) + 1):
                if j < 10:
                    j = f"0{j}"
                month_choices.append(f"{i}-{j}")
        return month_choices

    def _clean_region_choices(self, choices, regions):
        """
        Given the the two main inputs it will clean up the values to return the correct choices
        """

        if "Dublin" in regions.split(" ") or regions == "Dublin":
            # details=[f"D{i}" if str(i).isdigit() else i for i in geojson_details['Dublin Area']]
            details = "dublin_region"
        else:
            details = regions.lower()
        choices = self.clean_list(choices, self._area_options[details])

        return choices


#### tests ####
# model=InputModel()
# inputs={
#    'region':'Dublin',
#    'area': 'All',
#    'year':[2010,2018],
#    'months': [0,6],
#    'invert': [False]
# }
#
#
# model.cleanse_input(inputs)

if __name__ == "__main__":
    pass
