from dash import Dash, dcc, html
import pandas as pd
import plotly.express as px
import json

def filter_contest(df, column, candidates = []):
    return df[df[column].isin(candidates)]

def pivot(df, index, coulmn, value):
    return pd.pivot(df, index=index, columns=coulmn, values=value).rename_axis(columns=None).reset_index() # figure out how to keep voter turnout

#common typos:
#    - "# " instead of "#"
#    - "  " instead of " "
#    - "Boro" instead of "Borough" (EXCEPT DOYLESTOWN)
def fix_typos(df, column, old, new):
    df[column] = df[column].str.replace(old, new)
    return df

with open("data\Bucks_County_Voting_Precincts_2024.geojson") as f:
    precincts = json.load(f)
raw_df = pd.read_csv("data\Precincts_17(1).csv", skiprows=[0, 1])

cleaned = (
            raw_df.pipe(filter_contest, "Contest Name", ["Representative in Congress (Rep)"])
            .pipe(pivot, "nameplace", "Candidate Name", "Votes")
            .pipe(fix_typos, "nameplace", "# ", "#")
            .pipe(fix_typos, "nameplace", "  ", " ")
            .pipe(fix_typos, "nameplace", "Boro", "Borough")
          )

#figure out how to put this in the pipe block?
cleaned["Total"] = cleaned.sum(axis=1)
cleaned["Fitzpatrick Percentage"] = (cleaned["Brian Fitzpatrick"] / cleaned["Total"]) * 100
cleaned["Houck Percentage"] = (cleaned["Mark Houck"] / cleaned["Total"]) * 100
cleaned["Fitzpatrick Lead"] = (cleaned["Fitzpatrick Percentage"] - cleaned["Houck Percentage"])

def display_choropleth():
    fig = px.choropleth(cleaned, geojson=precincts, color="Fitzpatrick Lead",
                        locations="nameplace", featureidkey="properties.nameplace",
                        hover_name="nameplace",
                        hover_data=["Fitzpatrick Percentage", "Houck Percentage"],
                        color_continuous_scale=px.colors.diverging.RdBu,
                        color_continuous_midpoint=0,
                        projection="mercator")
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

#print(cleaned.head())

app = Dash(__name__)

app.layout = html.Div([
    html.H4('Republican Primary for Congress in Bucks County'),
    dcc.Graph(figure=display_choropleth()),
])

app.run_server(debug=True)

# fig = px.choropleth(cleaned, geojson=precincts, color="Fitzpatrick Lead",
#                     locations="nameplace", featureidkey="properties.nameplace",
#                     color_continuous_scale=px.colors.diverging.RdBu,
#                     color_continuous_midpoint=0,
#                     projection="mercator")
# fig.update_geos(fitbounds="locations", visible=False)
# fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
# fig.show()