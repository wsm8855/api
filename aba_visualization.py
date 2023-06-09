import json
import pickle
from urllib.request import urlopen

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

client_df = pd.read_csv("../../data/client_questionposts.csv")
with open("../../data/map_files.pickle", "rb+") as file:
    fips_grouped, cat_list, ethnic_list = pickle.load(file)

client_df["fips_codes"] = client_df["fips_codes"].replace(np.nan, 0)
client_df["fips_codes"] = client_df["fips_codes"].astype(float).astype(int).astype(str)
for idx, row in client_df.iterrows():
    if (len(row["fips_codes"]) < 5):
        client_df.at[idx, "fips_codes"] = "0" + row["fips_codes"]

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

dash_app = Dash(__name__, requests_pathname_prefix='/dash/')

dash_app.layout = html.Div([
    dcc.Link('Home Page', href='/', refresh=True),
    dcc.RadioItems(
        id='candidate',
        options=[],
        value="Coderre",
        inline=True
    ),
    dcc.Graph(id="graph"),
])


@dash_app.callback(Output("graph", "figure"), Input("candidate", "value"))
def display_choropleth(candidate):
    fips_grouped = client_df.groupby("fips_codes")
    df = pd.DataFrame(fips_grouped.groups.keys())
    df = df.rename(columns={0: "fips"})
    df['text'] = "State: " + fips_grouped["StateName_x"].max().values + '<br>' + \
                 "County: " + fips_grouped["County_x"].max().values + '<br>' + "Median Age: " + fips_grouped[
                     "Age_x"].median().values.astype(str) + \
                 "<br>Median Annual Income: " + fips_grouped["AnnualIncome_y"].median().values.astype(
        str) + "<br>---------------<br>Ethnicities:<br>---------------<br>" + ethnic_list + \
                 "<br>---------------<br>Categories:<br>---------------<br>" + cat_list
    df['usage'] = fips_grouped.size().values

    fig = go.Figure(data=go.Choropleth(
        geojson=counties,
        locations=df['fips'],
        z=df['usage'],
        zmax=df['usage'].quantile(0.95),
        zmin=df['usage'].quantile(0.05),
        locationmode='geojson-id',
        colorscale='Viridis',
        autocolorscale=True,
        text=df['text'],  # hover text
        marker_line_color='white',  # line markers between states
        colorbar_title="Individuals using ABA Pro Bono Services",
    ))

    fig.update_layout(
        title_text='ABA Pro Bono Categorical Distribution',
        geo=dict(
            scope='usa',
            projection=go.layout.geo.Projection(type='albers usa'),
            showlakes=False,  # lakes
            lakecolor='rgb(255, 255, 255)'),
        width=1250,
        height=750,
    )
    return fig
