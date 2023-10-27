import pandas as pd
import plotly.express as px

from utils.geojson_map_cleanse import DUBLIN_GEOJSON, PROVINCE_GEOJSON, COUNTY_GEOJSON


class GraphModel(object):
    """
    Object for returning the values for the various datarequest
    """

    def __init__(self):
        pass

    #### Backbone of GraphModel ####
    def import_data_model(self, model):
        """
        imports the data model for use with the graphs
        """
        self.data_object = model

    #### Utils ####
    @staticmethod
    def human_format(num, round_to=2):
        """
        _summary_

        Args:
            num (_type_): _description_
            round_to (int, optional): _description_. Defaults to 2.

        Returns:
            _type_: _description_
        """
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num = round(num / 1000.0, round_to)
        return "{:.{}f}{}".format(round(num, round_to), round_to, ["", "K", "M", "B", "T", "P"][magnitude])

    #### Graphs ####
    def scatter_map(self, animation=False, zoom=10):
        """
        Creates an scatter map with plotly express for displaying all the points on the map that were encoded
        Colour and size is set by price. Data can be stacked for entire view or split for animation
        """
        data = self.data_object.pull_data_query()
        if animation:
            fig = px.scatter_mapbox(
                data,
                lat="lat",
                lon="lon",
                color="price",
                size="price",
                color_continuous_scale=px.colors.sequential.Viridis,
                size_max=100,
                zoom=zoom,
                animation_frame="period",
                animation_group="price",
            )

            # Slows down the graph NOTE: https://community.plot.ly/t/how-to-slow-down-animation-in-plotly-express/31309/5
            fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 2000
        else:
            fig = px.scatter_mapbox(
                data,
                lat="lat",
                lon="lon",
                color="price",
                size="price",
                color_continuous_scale=px.colors.sequential.Viridis,
                size_max=100,
                zoom=zoom,
            )
            fig.update_mapboxes(style="open-street-map")
            fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig

    def line_chart(self, chart):
        """
        Returns the line chart
        """

        data = self.data_object.pull_grouped_data(grouping="period")

        colour = self.data_object.grouping_column.lower()
        # Series Chart Update

        # Line Charts
        if chart == "Line Chart - Total Value":
            graph = px.line(
                data,
                x="period",
                y="total_value",
                color=colour,
                height=350,
                labels={"period": "Period", "total_value": "Total Value", colour: colour.title()},
            )
        elif chart == "Line Chart - Average Price":
            graph = px.line(
                data,
                x="period",
                y="avg_price",
                color=colour,
                height=350,
                labels={"period": "Period", "avg_price": "Average Price", colour: colour.title()},
            )
        elif chart == "Line Chart - Volume of Sales":
            graph = px.line(
                data,
                x="period",
                y="num_of_sales",
                color=colour,
                height=350,
                labels={"period": "Period", "num_of_sales": "Volume of Sales", colour: colour.title()},
            )
        return graph

    def violin_chart(self, chart):
        """
        Returns the violin chart
        """
        data = self.data_object.pull_data_query()

        # Sets the colour
        colour = self.data_object.grouping_column

        # Violin Charts
        if chart == "Violin Chart - Price":
            graph = px.violin(data, y="price", color=colour, height=350, box=True, labels={"price": "Price"})

        return graph

    def bar_chart(self, chart, grouping=None):
        """
        Returns the bar chart grouped by the choice

        """
        # Starts to create the dict for the correct labels in the graph
        labels = {}
        catch = False

        # Sets the colour
        if "encoded_region" == self.data_object.grouping_column:
            catch = True

        colour = self.data_object.grouping_column

        # Adjusts the labels
        if grouping == "period":
            grouping = "period"
            labels["period"] = "Period"
        elif grouping == "year":
            grouping = "year"
            labels["year"] = "Year"

        # edit for grouping by region and dublin areas
        elif catch:
            labels["encoded_region"] = "Postal Codes"
            grouping = "encoded_region"
        else:
            labels[colour] = colour.title()
            grouping = colour.lower()

        # Pulls in the data based on the tick boxes for the grouping

        # Group by area
        if grouping.lower() == colour.lower():
            data = self.data_object.pull_grouped_data()

        # Group by year
        elif grouping == "year":
            data = self.data_object.pull_choices_grouped_by_year()

        # Group by period
        else:
            data = self.data_object.pull_grouped_data(grouping.lower())

        # Bar Charts
        if chart == "Bar Chart - Average Price":
            data = data.sort_values("avg_price")
            labels["avg_price"] = "Average Price"
            graph = px.bar(data, x=grouping, y="avg_price", color=colour, height=350, labels=labels)
        elif chart == "Bar Chart - Total Value":
            data = data.sort_values("total_value")
            labels["total_value"] = "Total Value"
            graph = px.bar(data, x=grouping, y="total_value", color=colour, height=350, labels=labels)
        elif chart == "Bar Chart - Volume of Sales":
            data = data.sort_values("num_of_sales")
            labels["num_of_sales"] = "Volume of Sales"
            graph = px.bar(data, x=grouping, y="num_of_sales", color=colour, height=350, labels=labels)
        return graph

    def choropleth_map(self):
        """
        Shows the breakdown for average price comparison across the country
        """
        # Pulls the market share data and creates the colour based off of the market share
        data = self.data_object.market_share_per_area()
        region = self.data_object.grouping_column

        # Cleans up the output for the user
        data["avg_price"] = data["avg_price"].apply(lambda x: GraphModel.human_format(x, 2))

        # NOTE: string format will make colour of regions on map discrete colour palete rather
        # data['total_value']=data['total_value'].apply(lambda x: GraphModel.human_format(x, 2))

        # Set the area for the map to focus on
        if region != "region":
            lats = 53.1424
            lons = -7.6921
            zoom = 5
        else:
            lats = 53.3498
            lons = -6.2603
            zoom = 10

        # Sorts out the assignement of regions from the dataset and the geojson
        if region == "province":
            geojson_key = "id"
            geojson = PROVINCE_GEOJSON
        elif region == "county":
            geojson_key = "id"
            geojson = COUNTY_GEOJSON
        else:
            geojson_key = "id"
            geojson = DUBLIN_GEOJSON

        geojson_key = f"properties.{geojson_key}"

        fig = px.choropleth_mapbox(
            data,
            geojson=geojson,
            locations=region.lower(),
            color="total_value",
            featureidkey=geojson_key,
            color_continuous_scale="Viridis",
            mapbox_style="carto-positron",
            zoom=zoom,
            center={"lat": lats, "lon": lons},
            opacity=0.8,
            hover_data=[region, "total_value", "market_share", "avg_price"],
            labels={
                "total_value": "Total Value",
                "avg_price": "Average Price",
                "market_share": "Market Share",
                region: region.title(),
            },
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig
