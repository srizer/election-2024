from dash import Dash, dcc, html
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
        return '<extra><span style="color:blue"><h1>+' + str(round(lead)) + "</h1></span></extra>"
    elif lead < 0:
        return '<extra><span style="color:red"><h1>+' + str(round(lead) * -1) + "</h1></span></extra>"
    else:
        return '<extra><span style="color:red"><h1>Tied</h1></span></extra>'

def create_hover_text(df, precinct, lead, candidates = []):
    text = '<span style="text-align:center;"><b>' + df[precinct] + "</b><br /><br />"
    for votes, pct in candidates:
        text += '<span style="display: block;float:right;">' + votes + ' <span style="display:block;">' + df[votes].astype(str) + " <b>" + df[pct].round(0).astype(int).astype(str) + "%" + "</b></span></span><br />"    
    text += df[lead]
    return text

#common typos:
#    - "# " instead of "#"
#    - "  " instead of " "
#    - "Boro" instead of "Borough" (EXCEPT DOYLESTOWN)
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

#figure out how to put this in the pipe block?
cleaned["Total"] = cleaned.sum(axis=1)
cleaned["Fitzpatrick Percentage"] = (cleaned["Brian Fitzpatrick"] / cleaned["Total"]) * 100
cleaned["Houck Percentage"] = (cleaned["Mark Houck"] / cleaned["Total"]) * 100
cleaned["Fitzpatrick Lead"] = (cleaned["Fitzpatrick Percentage"] - cleaned["Houck Percentage"])
cleaned["Clean Lead"] = cleaned["Fitzpatrick Lead"].apply(create_lead_text)
cleaned["hover"] = create_hover_text(
                        cleaned,
                        "nameplace",
                        "Clean Lead",
                        [
                            ( "Brian Fitzpatrick", "Fitzpatrick Percentage" ),
                            ( "Mark Houck", "Houck Percentage" )
                        ]                        
                    )

def display_choropleth():
    fig = go.Figure(
        data=go.Choropleth(
            geojson=precincts,
            locations=cleaned["nameplace"],
            z=cleaned["Fitzpatrick Lead"],
            featureidkey="properties.nameplace",
            colorscale=px.colors.diverging.BrBG,
            autocolorscale=False,
            zmid=0,
            hovertemplate=cleaned["hover"],            
            marker_line_color='white',
            colorbar_title="Fitzpatrick Lead"
        )
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(hoverlabel=dict(bgcolor="white"))
    return fig

app = Dash(__name__)

app.layout = html.Div([
    html.H1('Republican Primary for Congress in Bucks County'),
    dcc.Graph(figure=display_choropleth(), style={'width': '90vw', 'height': '90vh'}),  
])

server = app.server

if __name__ == '__main__':
    app.run(debug=True)