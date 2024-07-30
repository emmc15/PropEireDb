# SQL packages
import plotly.graph_objs as go
from colour import Color


def recursive_list_float_extractor(input_list):
    """
    _summary_

    Args:
        input_list (_type_): _description_

    Returns:
        _type_: _description_
    """

    returning_list = list()

    def inner_recusive_func(input):
        if isinstance(input, list):
            for i in input:
                if isinstance(i, float):
                    returning_list.append(input)
                else:
                    inner_recusive_func(i)

    inner_recusive_func(input_list)
    return returning_list


def colour_scale(num_of_steps, start_colour="red", end_colour="green"):
    """
    colour range split by percentage values

    Parameters:
    -----------
        start_colour=str(), beginning of colour range
        end_colour=str(), ending of colour range

    Returns:
    --------
        list(), a list of lists containing increasing value of step range and hex colour code
    """
    red = Color(start_colour)
    colors = list(red.range_to(Color(end_colour), num_of_steps))
    colors = [i.get_hex() for i in colors]
    value = (100 / num_of_steps) / 100
    j = 0
    colourscale = list()
    while j < num_of_steps:
        if j == 0:
            colourscale.append([0.0, colors[j]])
            percent = 0.0
        else:
            percent += value
            colourscale.append([percent, colors[j]])
        j = j + 1
    return colourscale


def colorscale_extractor(colourscale="Viridis"):
    """
    Generates the hex value from the colour scale provided by breakingup the colour scale from plotly dash

    Parameters:
    -----------
        data, float() less than 1 and greater than 0
        colourscale, str() of the colour scale plotly accepts

    Returns:
    -------
        str(), of hex code classification
    """
    # adds the centroids and the marker details back to the map
    graph_colour = go.Scattermapbox(
        # Irish center coordinates
        lat=[0],
        lon=[0],
        mode="markers",
        marker=dict(size=[5] * 11 + [8] * 11, color=0, colorbar=dict(title="Sample"), colorscale=colourscale),
    )

    colour_range = graph_colour["marker"]["colorscale"]

    extracted_colour_range = []
    for i in colour_range:
        extracted_colour_range.append([i[0], i[1]])
    return extracted_colour_range


def set_colour(percentage, colour="Viridis", greedy=True):
    """
    returns a colour hex code from a percentage value

    Parameters:
    -----------
        percentage=float(), percentage value
        colour=str(), plotly dash colour scale name
        num_of_steps=int(), number of steps in the colour scale
        greedy=boolean, whether another assignment of colour should happen between bands, else always lower band assignment
    Returns:
    --------
        str(), hex code of the percentage value in the plotly colour range defined
    """

    # Calls the colour scale range
    colors = colorscale_extractor(colourscale=colour)

    if percentage < 0.0 or percentage > 1.000001:
        raise TypeError("Please enter in a float value between 0.0 and 1.00001")

    for j in range(0, len(colors) - 1):
        # checks if value is between bands
        if percentage > colors[j][0] and percentage <= colors[j + 1][0]:
            if greedy is True:
                # Difference between bands
                diff_lower = percentage - colors[j][0]
                diff_higher = colors[j + 1][0]

                if diff_higher < diff_lower:
                    return colors[j + 1][1]
                else:
                    return colors[j][1]
            elif greedy is False:
                return colors[j][1]


if __name__ == "__main__":
    pass
