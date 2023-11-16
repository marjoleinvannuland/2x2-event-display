"""
A Dash app to display events in the 2x2 experiment
"""

# Import the required libraries
import dash_uploader as du
import plotly.graph_objects as go
import atexit
import shutil

from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import Output, DashProxy, Input, State, MultiplexerTransform

from display_utils import parse_contents, create_3d_figure

from os.path import basename
from pathlib import Path

# Settings and constants
UPLOAD_FOLDER_ROOT = "cache"

# Create the app
app = DashProxy(__name__, title="2x2 event display")
du.configure_upload(app, UPLOAD_FOLDER_ROOT)  # without this upload will not work

# App layout
app.layout = html.Div(
    [
        # Hidden divs to store data
        dcc.Location(id="url"),
        dcc.Store(id="filename", storage_type="session"),
        dcc.Store(id='data-length', data=0),
        # Header
        html.H1(children="2x2 event display", style={"textAlign": "center"}),
        html.Div(children="", id="filename-div", style={"textAlign": "center"}),
        # Upload button
        html.Div(
            du.Upload(
                id="upload-data-div",
                text="Upload Flow HDF5 File",
                max_file_size=10000,
                chunk_size=5,
                default_style={
                    "width": "15em",
                    "padding": "0",
                    "margin": "0",
                },
                pause_button=True,
                filetypes=["h5"],
            ),
        ),
        # Event ID input box
        dcc.Input(
                id="input-evid",
                type="number",
                placeholder="0",
                debounce=True,
                style={
                    "width": "6em",
                    "display": "inline-block",
                    "margin-right": "0.5em",
                    "margin-left": "0.5em",
                },
            ),
        # Event ID buttons
        html.Button('Previous Event', id='prev-button', n_clicks=0),
        html.Button('Next Event', id='next-button', n_clicks=0),
        dcc.Store(id='event-id', data=0),
        html.Div(id='evid-div', style={"textAlign": "center"}),
        # 3D graph
        dcc.Graph(id='3d-graph', style={'height': '70vh', 'width': '50vw'}),

        # MORE STUFF HERE
    ]
)


# Callbacks

# Callback to handle the upload
# =============================
@app.callback(
    [
        Output("filename", "data"),
        Output("filename-div", "children"),
        Output("event-id", "data", allow_duplicate=True),
        Output('data-length', 'data'),
    ],
    [
        Input("upload-data-div", "isCompleted"),
    ],
    [
        State("filename", "data"),
        State("upload-data-div", "fileNames"),
        State("upload-data-div", "upload_id"),
    ],
    prevent_initial_call=True
)
def upload_file(is_completed, filename, filenames, upload_id):
    """
    Upload HDF5 file to cache. If the upload is completed,
    update the filename. Initialise the event ID to 0.
    """
    if not is_completed:
        return filename, "no file uploaded", 0, 0

    if filenames is not None:
        if upload_id:
            root_folder = Path(UPLOAD_FOLDER_ROOT) / upload_id
        else:
            root_folder = Path(UPLOAD_FOLDER_ROOT)
        _, num_events = parse_contents(str(root_folder / filenames[0]))
        return str(root_folder / filenames[0]), basename(filenames[0]), 0, num_events

    return filename, "no file uploaded", 0, 0

# Callbacks to handle the event ID
# =================================
@app.callback(
    Output('event-id', 'data', allow_duplicate=True),
    Input('next-button', 'n_clicks'),
    State('event-id', 'data'),
    State('data-length', 'data'),
    prevent_initial_call=True
)
def increment(n, evid, max_value):
    if n > 0:
        new_evid = evid + 1
        if new_evid > max_value:  # wrap around
            return 0
        else:
            return new_evid

@app.callback(
    Output('event-id', 'data', allow_duplicate=True),
    Input('prev-button', 'n_clicks'),
    State('event-id', 'data'),
    State('data-length', 'data'),
    prevent_initial_call=True
)
def decrement(n, evid, max_value):
    if n > 0:
        if evid > 0:
            return evid - 1
        return max_value - 1 # wrap around

@app.callback(
    Output('event-id', 'data', allow_duplicate=True),
    Input('input-evid', 'value'),
    State('data-length', 'data'),
    prevent_initial_call=True
)
def set_evid(value, max_value):
    if value is not None:
        if value > max_value:  # not possible to go higher than max value
            return max_value
        else:
            return value

@app.callback(
    Output('evid-div', 'children'),
    Input('event-id', 'data'),
    State('data-length', 'data'),
)
def update_div(evid, max_value):
    return f'Event ID: {evid}/{max_value}'

# Callback to display the event
# =============================
@app.callback(
    Output('3d-graph', 'figure'),
    Input('filename', 'data'),
    Input('event-id', 'data'),
    prevent_initial_call=True
)
def update_graph(filename, evid):
    # TODO: fix, this gives an error if the cache is cleaned, since the filename is not reset to None
    if filename is not None:
        data, _ = parse_contents(filename)
        return create_3d_figure(data, evid)



# Cleaning up
# ===========
@atexit.register
def clean_cache():
    """Delete uploaded files"""
    try:
        shutil.rmtree(Path(UPLOAD_FOLDER_ROOT))
    except OSError as err:
        print("Can't clean %s : %s" % (UPLOAD_FOLDER_ROOT, err.strerror))

# Run the app
if __name__ == "__main__":
    app.run(debug=True, port=8080)
