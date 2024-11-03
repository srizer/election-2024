from dash import Dash, dcc, html
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.request, json

def filter_contest(df, column, candidates = []):
    return df[df[column].isin(candidates)]

def pivot(df, index, coulmn, value):
    return pd.pivot(df, index=index, columns=coulmn, values=value).rename_axis(columns=None).reset_index() # figure out how to keep voter turnout

def create_lead_text(lead):
    if lead > 0:
        return '<br /><span style="color:blue;"><b>Fitzpatrick +' + str(round(lead)) + "</b></span></span><extra></extra>"
    elif lead < 0:
        return '<br /><span style="color:red;"><b>Houck +' + str(round(lead) * -1) + "</b></span></span><extra></extra>"
    else:
        return '<br /><span style="color:black;"><b>Tied</b></span></span><extra></extra>'
    
def create_spacing(num):
    return " " * num

def create_hover_text(df, precinct, lead, candidates = []):
    text = ""
    text += '<br /><span style="font-family: Overpass, monospace; color:black;"><b>' + df[precinct] + "</b><br /><br />"
    for votes, pct, space in candidates:
        text += votes + space + df[votes].astype(str) + " <b>" + df[pct].round(0).astype(int).astype(str) + "%" + "</b><br />"
    text += df[lead]
    return text

# common typos:
#     - "# " instead of "#"
#     - "  " instead of " "
#     - "Boro" instead of "Borough" (EXCEPT DOYLESTOWN)
def fix_typos(df, column, old, new):
    df[column] = df[column].str.replace(old, new)
    return df

# make these env vars or something idk
with urllib.request.urlopen("https://gist.githubusercontent.com/srizer/c26b7fb3c34546ee4d3b9a71bdefced7/raw/09ade6ce26624d63ce8216d9fba82e0cd26f14f4/Bucks_County_Voting_Precincts_2024.geojson") as url:
    precincts = json.load(url)
raw_df = pd.read_csv("https://gist.githubusercontent.com/srizer/5280257d7a6ad8be2f3a8e85524d74a0/raw/d9039edf9d5e3797f4094ed20729e1cc691a258c/Precincts_17(1).csv", skiprows=[0, 1])

cleaned = (
            raw_df.pipe(filter_contest, "Contest Name", ["Representative in Congress (Rep)"])
            .pipe(pivot, "nameplace", "Candidate Name", "Votes")
            .pipe(fix_typos, "nameplace", "# ", "#")
            .pipe(fix_typos, "nameplace", "  ", " ")
            .pipe(fix_typos, "nameplace", "Boro", "Borough")
        )

bins = [-np.inf, -50, -25, -10, 0, 10, 25, 50, np.inf]
labels = ["Houck >50%", "Houck 25-50%", "Houck 10-25%", "Houck 0-10%", "Fitzpatrick 0-10%", "Fitzpatrick 10-25%", "Fitzpatrick 25-50%", "Fitzpatrick >50%"]
color_scale = ["#c93135", "#db7171", "#eaa9a9", "#fce0e0", "#ceeafd", "#92bde0", "#5295cc", "#1375b7"]
pairs = dict(zip(labels, color_scale))

# figure out how to put this in the pipe block?
# also this is disgusting code lol i should have used js
cleaned["Total"] = cleaned.sum(axis=1)
cleaned["Fitzpatrick Percentage"] = (cleaned["Brian Fitzpatrick"] / cleaned["Total"]) * 100
cleaned["Houck Percentage"] = (cleaned["Mark Houck"] / cleaned["Total"]) * 100
cleaned["Fitzpatrick Lead"] = (cleaned["Fitzpatrick Percentage"] - cleaned["Houck Percentage"])
cleaned["Binned Lead"] = pd.cut(cleaned["Fitzpatrick Lead"], bins=bins, labels=labels)
cleaned["Clean Lead"] = cleaned["Fitzpatrick Lead"].apply(create_lead_text)
cleaned["Digit Difference"] = 11 + (cleaned["Brian Fitzpatrick"].astype(str).str.len() - cleaned["Mark Houck"].astype(str).str.len()).astype(int)
cleaned["Space Padding"] = cleaned["Digit Difference"].apply(create_spacing)
cleaned["hover"] = create_hover_text(
                        cleaned,
                        "nameplace",
                        "Clean Lead",
                        [
                            ( "Brian Fitzpatrick", "Fitzpatrick Percentage", "    " ),
                            ( "Mark Houck", "Houck Percentage",  cleaned["Space Padding"])
                        ]                        
                    )

def display_barchart(df, a, b):
    a_total = df[a].sum()
    b_total = df[b].sum()
    fig = go.Figure(
        go.Bar(
            x=[a, b],
            y=[a_total, b_total]
        )
    )
    return fig

def display_choropleth(df, z):
    fig = px.choropleth_map(
        df,
        geojson=precincts,
        locations=df["nameplace"],
        color=df[z],
        color_discrete_map=pairs,
        featureidkey="properties.nameplace",
        map_style="carto-positron",
        center={ "lat": 40.309659650050946, "lon": -75.11666494467029 },
        zoom=9.5,
        hover_data={ "Binned Lead": False, "nameplace": False, "hover": True },
        # hover_name=" "
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(hovermode="x")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})    
    fig.update_layout(hoverlabel=dict(bgcolor="white"))
    fig.update_layout(
        hoverlabel=dict(
            font_color="white"  # Hack to compensate for inability to remove "hover=" from hover
        )
    )
    fig.update_layout(
        legend_title_text="Candidate Lead",
        legend=dict(
            font=dict(
                family="Overpass, monospace",
                size=18,
                color="black"
            )
        )
    )
    return fig

app = Dash(__name__, external_stylesheets=['assets/style.css'])

app.layout = html.Div([
    html.H1('Republican Primary for Congress in Bucks County'),
    html.Div([
        dcc.Graph(figure=display_barchart(cleaned, "Brian Fitzpatrick", "Mark Houck"), config={'displayModeBar': False})
    ], style={'width': '40%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(figure=display_choropleth(cleaned, "Binned Lead"), style={'height': '90vh'}, config={'displayModeBar': False}),
    ], style={'width': '60%', 'display': 'inline-block', 'padding': '0 20'})     
])

server = app.server

if __name__ == '__main__':
    app.run(debug=True)