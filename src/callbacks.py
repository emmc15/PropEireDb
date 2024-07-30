"""
main logic of dashboard
"""
import json
from datetime import datetime
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from sqlalchemy import text


from layout import layout  # noqa
from models.data_model import DataModel
from models.graph_model import GraphModel
from models.input_model import InputModel
from server_config import application, PG_ALCHEMY_CONNECTION, REDIS_TIMEOUT, CACHE

# -----------------------------------------------------------------------------
# Model Creation for Startup
# -----------------------------------------------------------------------------

inputs = {
    "region": "Province",
    "area": "Dublin",
    "year": [2010, datetime.now().year],
    "months": [0, 11],
    "invert": [True],
}


# Connects to database PG_CONNECTION for pulling column values
input_model = InputModel(PG_ALCHEMY_CONNECTION)

# Imports the PG_CONNECTION for conneting to db NOTE: PG_CONNECTION is defined in keys.py
data_model = DataModel(input_model, PG_ALCHEMY_CONNECTION)
# data_model.import_json(inputs)

# model used to generate the graphs
graph_model = GraphModel()

# Pulls in all the choices options
choices = dict()
for i in ["county", "province", "dublin_region"]:
    if i != "dublin_region":
        query = f"SELECT distinct({i}) from propeiredb.residential_register"
        column_assigned = i
    else:
        query = "SELECT distinct(region) from propeiredb.residential_register_dublin_mapped"
        column_assigned = "region"

    groups = pd.read_sql(text(query), con=PG_ALCHEMY_CONNECTION.connect())
    listing = list(groups[column_assigned])
    listings_cleansed = ["All"]

    for j in listing:
        j = str(j).title()
        if "None" not in j:
            listings_cleansed.append(j)

    choices[i] = [{"label": x, "value": x} for x in listings_cleansed]


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------


# Drives the second dropdown by the available options from the first province one
@application.callback(Output("region-choice-dropdown", "options"), [Input("region-dropdown", "value")])
@CACHE.memoize(timeout=6000)
def set_region_dropdown_options(selected_region):
    """
    _summary_

    Args:
        selected_region (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Adding in all feature
    if "Dublin" in selected_region:
        area = choices["dublin_region"]
    else:
        area = choices[selected_region.lower()]
    return area


# sets the value of the second dropdown
@application.callback(Output("region-choice-dropdown", "value"), [Input("region-choice-dropdown", "options")])
def set_region_value(available_options):
    """
    _summary_

    Args:
        available_options (_type_): _description_

    Returns:
        _type_: _description_
    """
    return "All"


@application.callback(
    Output("cached-inputs", "children"),
    [
        Input("region-dropdown", "value"),
        Input("region-choice-dropdown", "value"),
        Input("invert-region-choice", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date")
        # Input("year-choice-dropdown", "value"),
        # Input("time-of-year-choice-dropdown", "value"),
    ],
)
def cached_inputs(region, area, invert, start_date, end_date):
    """
    Converts all the base inputs into json dumped into the webpage. This is done to create a chained callback for all graphs to update on change
    and reduce the amount of code and lines in the file
    NOTE: https://dash.plot.ly/sharing-data-between-callbacks
    """

    inputs = {"region": region, "area": area, "start_date": start_date, "end_date": end_date, "invert": invert}

    return json.dumps(inputs)


@application.callback(
    Output("track-annoying-alert", "data"), Input("warning-alert", "is_open"), State("track-annoying-alert", "data")
)
def track_annoying_alert(state_of_alert: bool, has_it_been_opened: bool):
    if has_it_been_opened is None:
        has_it_been_opened = False
    if state_of_alert is True and has_it_been_opened is False:
        has_it_been_opened = True

    return has_it_been_opened


@application.callback(
    Output("warning-alert", "is_open"),
    Input("region-dropdown", "value"),
    State("track-annoying-alert", "data"),
)
def alert_pop_up(region, dismissed_already):
    state = False
    if "dublin" in region.lower() and dismissed_already is False:
        state = True

    return state


# -----------------------------------------------------------------------------
# Graphs
# -----------------------------------------------------------------------------


@application.callback(
    Output("mapbox", "figure"), [Input("cached-inputs", "children"), Input("region-dropdown", "value")]
)
@CACHE.memoize(timeout=600)
def update_map(cache, region):
    """
    _summary_

    Args:
        button_press (_type_): _description_
        cache (_type_): _description_
        region (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Graph Cache
    loads = json.loads(cache)  # Loads in local stored cache
    # key = "{}:{}".format("update_map", loads["key"])  # Generates key for func

    data_model.import_json(loads)
    graph_model.import_data_model(data_model)

    if region == "Dublin Clustering":
        # return scatter_map(region, choice, year, period, invert=invert)
        graph = graph_model.scatter_map(zoom=9)
    else:
        graph = graph_model.choropleth_map()

    return graph


# Shows the bars under the graph choices
@application.callback(Output("left-checkbox", "style"), [Input("left-chart-dropdown", "value")])
@CACHE.memoize(timeout=REDIS_TIMEOUT)
def update_left_group(chart):
    """
    _summary_

    Args:
        chart (_type_): _description_

    Returns:
        _type_: _description_
    """
    if "Bar" in chart:
        return {"display": "inline-block"}
    return {"display": "none"}


@application.callback(Output("series-checkbox", "style"), [Input("chart-dropdown", "value")])
@CACHE.memoize(timeout=REDIS_TIMEOUT)
def update_series_group(chart):
    """
    _summary_

    Args:
        chart (_type_): _description_

    Returns:
        _type_: _description_
    """
    if "Bar" in chart:
        return {"display": "inline-block"}
    return {"display": "none"}


@application.callback(Output("right-checkbox", "style"), [Input("right-chart-dropdown", "value")])
@CACHE.memoize(timeout=REDIS_TIMEOUT)
def update_right_group(chart):
    """
    _summary_

    Args:
        chart (_type_): _description_

    Returns:
        _type_: _description_
    """
    if "Bar" in chart:
        return {"display": "inline-block"}
    return {"display": "none"}


@application.callback(
    Output("series-chart", "figure"),
    [Input("chart-dropdown", "value"), Input("series-checkbox", "value"), Input("cached-inputs", "children")],
)
@CACHE.memoize(timeout=REDIS_TIMEOUT)
def series_chart(chart, agg, cache):
    """
    Takes in the normal values and as well as a chart value which will allow it to change chart in return
    """

    # Graph Cache
    loads = json.loads(cache)  # Loads in local stored cache
    # if agg == None:
    #     key = "{}:{}".format(chart, loads["key"])
    # else:
    #     key = "{}:{}:{}".format(chart, agg, loads["key"])  # Generates key for func

    data_model.import_json(loads)
    graph_model.import_data_model(data_model)

    if "Line Chart" in chart:
        graph = graph_model.line_chart(chart)
    elif "Violin Chart" in chart:
        graph = graph_model.violin_chart(chart)
    elif "Bar Chart" in chart:
        graph = graph_model.bar_chart(chart, grouping=agg)

    return graph


@application.callback(
    Output("left-chart", "figure"),
    [Input("left-chart-dropdown", "value"), Input("left-checkbox", "value"), Input("cached-inputs", "children")],
)
@CACHE.memoize(timeout=REDIS_TIMEOUT)
def left_chart(chart, agg, cache):
    """
    Takes in the normal values and as well as a chart value which will allow it to change chart in return
    """
    # Graph Cache
    loads = json.loads(cache)  # Loads in local stored cache
    # if agg == None:
    #     key = "{}:{}".format(chart, loads["key"])
    # else:
    #     key = "{}:{}:{}".format(chart, agg, loads["key"])  # Generates key for func

    data_model.import_json(loads)
    graph_model.import_data_model(data_model)

    if "Line Chart" in chart:
        graph = graph_model.line_chart(chart)
    elif "Violin Chart" in chart:
        graph = graph_model.violin_chart(chart)
    elif "Bar Chart" in chart:
        graph = graph_model.bar_chart(chart, grouping=agg)

    return graph


@application.callback(
    Output("right-chart", "figure"),
    [Input("right-chart-dropdown", "value"), Input("right-checkbox", "value"), Input("cached-inputs", "children")],
)
@CACHE.memoize(timeout=REDIS_TIMEOUT)
def right_chart(chart, agg, cache):
    """
    Takes in the normal values and as well as a chart value which will allow it to change chart in return
    """
    # Graph Cache
    loads = json.loads(cache)  # Loads in local stored cache

    data_model.import_json(loads)
    graph_model.import_data_model(data_model)

    if "Line Chart" in chart:
        graph = graph_model.line_chart(chart)
    elif "Violin Chart" in chart:
        graph = graph_model.violin_chart(chart)
    elif "Bar Chart" in chart:
        graph = graph_model.bar_chart(chart, grouping=agg)

    return graph


@application.callback(Output("total-value", "children"), [Input("cached-inputs", "children")])
@CACHE.memoize(timeout=REDIS_TIMEOUT)
def total_value(cache):
    """
    total value by region and choices and period selection
    """
    data_model.import_json(json.loads(cache))
    value = data_model.total_query("sum")
    return graph_model.human_format(value)


@application.callback(Output("volume-value", "children"), [Input("cached-inputs", "children")])
@CACHE.memoize(timeout=REDIS_TIMEOUT)
def volume_value(cache):
    """
    total value by region and choices and period selection
    """
    data_model.import_json(json.loads(cache))
    value = data_model.total_query("count")
    return graph_model.human_format(value)


@application.callback(Output("avg-value", "children"), [Input("cached-inputs", "children")])
@CACHE.memoize(timeout=REDIS_TIMEOUT)
def avg_value(cache):
    """
    total value by region and choices and period selection
    """
    data_model.import_json(json.loads(cache))
    value = data_model.total_query("avg")
    return graph_model.human_format(value)


@application.callback(Output("pie-chart", "figure"), [Input("cached-inputs", "children")])
@CACHE.memoize(timeout=REDIS_TIMEOUT)
def pie_chart(cache):
    """
    Pie chart of two colours, one of the selected regions and one for all regions both reprented in a given period
    """

    # Graph Cache
    loads = json.loads(cache)  # Loads in local stored cache

    data_model.import_json(loads)
    data = data_model.market_share_selected()
    fig = px.pie(
        data,
        values="market_share",
        names="choice",
        color_discrete_sequence=px.colors.sequential.Viridis[::-1],
        hover_data=["market_share"],
        labels={"market_share": "Market Share", "choice": "Choice"},
        hole=0.3,
    )
    fig.update_layout(margin=go.layout.Margin(l=5, r=5, b=5, t=5))

    return fig


if __name__ == "__main__":
    # application.run_server(port=8000, host='0.0.0.0', threaded=True, debug=True) #NOTE: for dev use
    pass
