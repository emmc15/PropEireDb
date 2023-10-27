from datetime import datetime
import os
import base64

import dash_bootstrap_components as dbc
from dash import dcc
from dash import html

from server_config import application

#### CSS Theme Variables ####
setting = "dark"

if setting == "light":
    nav_bar_css = "navbar navbar-expand-lg navbar-light bg-primary"
    summary_cards_css = "card text-white bg-secondary mb-3"
else:
    nav_bar_css = "navbar navbar-expand-lg navbar-dark bg-dark"
    div_main_css = "card text-white bg-primary mb-3"
    summary_cards_css = "card text-white bg-success mb-3"

#### Setting the variables #####

# List for charts
chart = ["Line Chart", "Violin Chart", "Bar Chart"]
graphs = ["Total Value", "Average Price", "Volume of Sales"]
charts = []
for i in chart:
    if i != "Violin Chart":
        for j in graphs:
            charts.append("{} - {}".format(i, j))
    else:
        charts.append("Violin Chart - Price")


#### Navbar Simple ####
navbar_simple = dbc.NavbarSimple(
    children=[
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Menu",
            children=[
                # dbc.DropdownMenuItem("GitHub", href="https://github.com/emmc15"),
                # dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("Support this website", href="https://www.buymeacoffee.com/propeiredb"),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem(
                    "Property Register Site",
                    href="https://propertypriceregister.ie/website/npsra/pprweb.nsf/PPR?OpenForm",
                ),
                # dbc.DropdownMenuItem(divider=True),
                # dbc.DropdownMenuItem("CSS Theme", href="https://bootswatch.com/flatly/"),
            ],
        )
    ],
    brand="PropEireDB",
    sticky="top",
    className=nav_bar_css,
    id="nav-bar",
)
# make dropdown for the link referneces in the page
dropdown = dbc.DropdownMenu(
    children=[
        # NOTE: target parameter opens link in new tab rather than override this
        dbc.DropdownMenuItem("Buy Me a Coffee", href="https://www.buymeacoffee.com/propeiredb"),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem(
            "Property Register Site", href="https://propertypriceregister.ie/website/npsra/pprweb.nsf/PPR?OpenForm"
        ),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem("Contact Us", href="mailto:admin@propeiredb.ie"),
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem("T&Cs of PRSA Data Used", href="http://psr.ie/en/PSRA/Pages/Re-Use_of_Information"),
    ],
    nav=True,
    in_navbar=True,
    label="Menu",
    size="sm",
    right=True,
)


#### Navbar Complex ####
# Base Navbar insert layout
base_navbar = dbc.Container(
    [
        # Sets the branding and the title
        dbc.Row(
            [
                # Imports the logo to the navbar NOTE: app.get_asset_url() searches for asset folder in python and pulls in the png image
                dbc.Col(html.Img(src=application.get_asset_url("white-home-6-point-see-through.png"), height="40px")),
                dbc.Col(dbc.NavbarBrand("PropEireDB")),
            ],
            align="left",
        ),
        # Sets the navbar to be collapsible for mobile view ie. menu dropdown on mobile
        dbc.NavbarToggler(id="navbar-toggler"),
        # Adds in the dropdown for the collapse on mobile
        dbc.Collapse(
            dbc.Nav([dropdown], className=nav_bar_css, navbar=True, horizontal="end"), id="navbar-collapse", navbar=True
        ),
    ]
)

# Final creation of the nav bar
navbar_complex = dbc.Navbar(base_navbar, id="nav-bar", className=nav_bar_css, color="green")


#### Region Selection #####

# Region Choice
region_choice = html.Div(
    [
        html.H6("Select Map Type"),
        dcc.Dropdown(
            id="region-dropdown",
            options=[
                {"label": "Province", "value": "Province"},
                {"label": "County", "value": "County"},
                {"label": "Dublin Area", "value": "Dublin Area"},
                {"label": "Dublin Scatter Map", "value": "Dublin Clustering"},
            ],
            value="Province",
            style={"width": "75%", "display": "inline-block"}
            # inputStyle={"margin-right": "2px", "margin-left": "5px"},
            # labelStyle={"display": "inline-block", "margin-left": "50px"},
        ),
    ],
    style={"margin-left": "50px"},
)

#### Area Choice ####
# This selects the area based on the region choice selection
area_choice = html.Div(
    [
        # Area Choice Dropdown
        html.H3(),
        html.H6("Select Areas"),
        dcc.Dropdown(id="region-choice-dropdown", multi=True, style={"width": "75%", "display": "inline-block"}),
    ],
    style={"margin-left": "50px"},
)

#### Invert Area Selection ####
invert_choice = html.Div(
    [
        dcc.Checklist(
            id="invert-region-choice",
            options=[{"label": "Invert Selection", "value": True}],
            inputStyle={"margin-right": "2px", "margin-left": "5px"},
            labelStyle={"display": "inline-block", "margin-left": "50px"},
        )
    ]
)

##### Year Slider ####
# Select the year via slider
year_slider = html.Div(
    [
        html.H6("Year Slider"),
        dcc.Dropdown(id="year-choice-dropdown", multi=True, options=[str(i) for i in range(2010, 2023)], value="2022"),
    ],
    style={"margin-left": "50px", "margin-right": "50px", "margin-bottom": "50px"},
)

#### Period Slider ####

# Select the periods via slider
period_slider = html.Div(
    [
        html.H6("Month Slider"),
        dcc.RangeSlider(
            id="time-of-year-choice-dropdown",
            min=0,
            max=11,
            step=None,
            marks={
                0: "Jan",
                1: "Feb",
                2: "Mar",
                3: "Apr",
                4: "May",
                5: "Jun",
                6: "Jul",
                7: "Aug",
                8: "Sep",
                9: "Oct",
                10: "Nov",
                11: "Dec",
            },
            value=[0, 11],
        ),
    ],
    style={"margin-left": "50px", "margin-right": "50px", "margin-bottom": "50px"},
)


date_picker = dcc.DatePickerRange(
    id="date-range",
    start_date_placeholder_text="Start Period",
    end_date_placeholder_text="End Period",
    calendar_orientation="vertical",
    start_date=datetime(2010, 1, 1),
    end_date=datetime.today(),
)

date_picker = html.Div(
    [html.H6("Date Range"), date_picker], style={"margin-left": "50px", "margin-right": "50px", "margin-bottom": "50px"}
)

#### Update Map Button ####

# Button Div
update_button = html.Div(
    [
        # Adds the button for updating the map
        html.Button(id="graph-button", n_clicks=0, children="Update Map", className="btn btn-outline-success")
    ],
    style={"width": "100%", "display": "flex", "align-items": "center", "justify-content": "center"},
)

#### Input Area ####

# Formats the html in single div with breaks between inputs
input_column = html.Div(
    [
        region_choice,
        html.Br(),
        area_choice,
        invert_choice,
        html.Br(),
        date_picker,
        # html.Br(),
        # year_slider,
        # html.Br(),
        # period_slider,
        # update_button,
        html.Br(),
    ]
)

# Converts to column and sets the widths for reformatting on different screens
# input_column = dbc.Col([input_column], width=2, md=2, lg=2, xl=2, sm=12, xs=12)

#### Map Column ####
# Map Column
# map_column=dbc.Col(
#    #Loading component to show user map is loading in long wait times
#    dcc.Loading(id='map-loading',
#        children=[dcc.Graph(id='mapbox', style={"width": "75%", 'height':'100%', "display": "inline-block"})],
#        type='cirlce',
#        color='#18BC9C'),
#    width=6, md=6, lg=6,xl=6,sm=12,xs=12
# )

# Used below instead as issue with loading object and hover data
# NOTE: https://community.plot.ly/t/choroplethmapbox-hover-problem/33218
new_map_column = dbc.Col(
    # Loading component to show user map is loading in long wait times
    html.Div(
        [
            dcc.Graph(id="mapbox", style={"width": "100%", "height": "800px", "display": "inline-block"}),
        ],
        style={"margin-left": "30px"},
    ),
    width=8,
    md=12,
    lg=8,
    xl=8,
    sm=12,
    xs=12,
)


#### Stacked High Level metrics ####
# Stacked Values
stacked_values = dbc.Col(
    [
        # Total Value
        html.Div(
            [
                html.H6("Total Value", style={"text-align": "center"}),
                html.H4(id="total-value", className="info-text", style={"text-align": "center"}),
            ],
            id="total",
            className=summary_cards_css,
        ),
        # Number of Sales
        html.Div(
            [
                html.H6("No. of Sales", style={"text-align": "center"}),
                html.H4(id="volume-value", className="info-text", style={"text-align": "center"}),
            ],
            id="count",
            className=summary_cards_css,
        ),
        # Average Price
        html.Div(
            [
                html.H6("Average Price", style={"text-align": "center"}),
                html.H4(id="avg-value", className="info-text", style={"text-align": "center"}),
            ],
            id="avg",
            className=summary_cards_css,
        ),
        # Pie Chart
        html.Div([dcc.Graph(id="pie-chart", style={"width": "100%", "height": "200px", "display": "inline-block"})]),
        # Inputs
        html.Div([input_column]),
    ],
    width=3,
    md=12,
    lg=3,
    xl=3,
    sm=12,
    xs=12,
)

#### First Row ####
annoying_alert = dbc.Alert(
    "Data shown has missing entries and inaccuarcies, to help improve the system and keep it up to date and free from ads, please consider donating at https://www.buymeacoffee.com/propeiredb",
    id="warning-alert",
    dismissable=True,
    is_open=False,
    fade=True,
    class_name="alert alert-dismissable alert-danger",
)
first_row = html.Div([annoying_alert, html.Br(), dbc.Row([new_map_column, stacked_values], justify="center")])

#### First Graph Area ####
# top left graph and dropdown
first_graph = dbc.Col(
    [
        # Sets the dropdown for the selection of what type of graph
        dcc.Dropdown(
            id="left-chart-dropdown",
            options=[{"label": k, "value": k} for k in charts],
            value="Bar Chart - Total Value",
            style={"width": "75%", "display": "inline-block", "margin-left": "25px"},
        ),
        # Optional radio buttons to allow greater choice graphing potential
        dcc.RadioItems(
            id="left-checkbox",
            options=[
                {"label": "  Grouped by year  ", "value": "year"},
                {"label": "  Grouped by period  ", "value": "period"},
                {"label": "  Grouped by Area  ", "value": "area"},
            ],
            value="area",
            labelStyle={"display": "inline-block", "margin-left": "50px"},
            inputStyle={"margin-right": "1px", "margin-left": "5px"},
        ),
        # Graph layout object
        dcc.Graph(id="left-chart", style={"width": "100%", "height": "300px", "display": "inline-block"}),
    ],
    width={"size": 6},
    md=6,
    lg=6,
    xl=6,
    sm=12,
    xs=12,
)

#### Second Graph Area #####
second_graph = dbc.Col(
    [
        dcc.Dropdown(
            id="right-chart-dropdown",
            options=[{"label": k, "value": k} for k in charts],
            value="Bar Chart - Volume of Sales",
            style={"width": "75%", "display": "inline-block", "margin-left": "25px"},
        ),
        dcc.RadioItems(
            id="right-checkbox",
            options=[
                {"label": "  Grouped by year  ", "value": "year"},
                {"label": "  Grouped by period  ", "value": "period"},
                {"label": "  Grouped by Area  ", "value": "area"},
            ],
            value="area",
            labelStyle={"display": "inline-block", "margin-left": "50px"},
            inputStyle={"margin-right": "1px", "margin-left": "5px"},
        ),
        dcc.Graph(id="right-chart", style={"width": "100%", "height": "300px", "display": "inline-block"}),
    ],
    width={"size": 6},
    md=6,
    lg=6,
    xl=6,
    sm=12,
    xs=12,
)

#### Second Row ####
second_row = html.Div([dbc.Row([first_graph, second_graph], justify="around")])

#### Bottom Graph ####
bottom_graph = dbc.Col(
    [
        # Dropdown for choicing the graph
        dcc.Dropdown(
            id="chart-dropdown",
            options=[{"label": k, "value": k} for k in charts],
            value="Line Chart - Total Value",
            style={"width": "75%", "display": "inline-block", "margin-left": "25px"},
        ),
        # Hidden radio items to extend out the functionality of specific graphs
        dcc.RadioItems(
            id="series-checkbox",
            options=[
                {"label": "  Grouped by year  ", "value": "year"},
                {"label": "  Grouped by period  ", "value": "period"},
                {"label": "  Grouped by Area  ", "value": "area"},
            ],
            value="area",
            labelStyle={"display": "inline-block", "margin-left": "50px"},
            inputStyle={"margin-right": "1px", "margin-left": "5px"},
        ),
        # graphing object
        dcc.Graph(id="series-chart", style={"width": "100%", "height": "300px", "display": "inline-block"}),
    ]
)

#### Third Row ####
third_row = html.Div([html.Br(), dbc.Row([bottom_graph])])

# -----------------------------------------------------------------------------
# Layout Config
# -----------------------------------------------------------------------------

# buymeacoffee footer
image_filename = "bmc-full-logo-no-background.png"
image_filepath = os.path.join(os.getcwd(), "assets", image_filename)
with open(image_filepath, "rb") as img:
    encoded_image = base64.b64encode(img.read())

buymeacoffee_image = html.A(
    [html.Img(src="data:image/png;base64,{}".format(encoded_image.decode()), height=100, width=200)],
    href="https://www.buymeacoffee.com/propeiredb",
    style={"display": "inline-block"},
)

mail_to_footer = html.A("Contact Us at admin@propeiredb.ie", href="mailto:admin@propeiredb.ie")
use_of_data = html.A("T&Cs of PRSA Data Used", href="http://psr.ie/en/PSRA/Pages/Re-Use_of_Information")
buymeacoffee_image = dbc.Container(
    dbc.Row(
        [
            dbc.Col(
                [html.Br(), buymeacoffee_image, html.Br(), mail_to_footer, html.Br(), use_of_data],
                width=3,
                md=3,
                lg=3,
                xl=3,
                sm=12,
                xs=12,
            )
        ],
        align="center",
        justify="center",
    ),
)

#### Cached Div ####
geojson_div = html.Div(id="cached-geojson", style={"display": "none"})
inputs_div = html.Div(id="cached-inputs", style={"display": "none"})


#### Layout ####
navbar = navbar_complex
footer = html.Div([html.Br(), buymeacoffee_image])
layout = html.Div(
    [
        navbar,
        first_row,
        second_row,
        third_row,
        footer,
        geojson_div,
        inputs_div,
        dcc.Store(id="track-annoying-alert", storage_type="memory"),
    ]
)

#### Insert into Server ####
application.layout = layout  # Assigns the layout
application.title = "PropEireDB"
