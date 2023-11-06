"""
A Dash app to display events in the 2x2 experiment
"""

import dash

app = dash.Dash(__name__, title="2x2 event display")

app.layout = dash.html.Div(
    [dash.html.H1(children="2x2 event display", style={"textAlign": "center"})]
)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
