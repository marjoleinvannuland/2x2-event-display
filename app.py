"""
A Dash app to display events in the 2x2 experiment
"""

# Import the required libraries
import dash_uploader as du

from dash import dcc
from dash import html
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import Output, DashProxy, Input, State, MultiplexerTransform

from display_utils import process_uploaded_hdf5

from os.path import basename
from pathlib import Path

# Settings and constants
UPLOAD_FOLDER_ROOT = "cache"

# Create the app
app = DashProxy(__name__, title="2x2 event display")
du.configure_upload(app, UPLOAD_FOLDER_ROOT)  # without this upload will not work

app.layout = html.Div(
    [
        # Hidden divs to store data
        dcc.Location(id="url"),
        dcc.Store(id="filename", storage_type="session"),
        dcc.Store(id="event-id", storage_type="session"),
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
        # MORE STUFF HERE
    ]
)


# Callbacks
@app.callback(
    [
        Output("filename", "data"),
        Output("filename-div", "children"),
        Output("event-id", "data"),
    ],
    [
        Input("upload-data-div", "isCompleted"),
    ],
    [
        State("filename", "data"),
        State("upload-data-div", "fileNames"),
        State("upload-data-div", "upload_id"),
    ],
)
def upload_file(is_completed, filename, filenames, upload_id):
    """
    Upload HDF5 file to cache. If the upload is completed,
    process the file and update the filename. Initialise the event ID to 0.
    """
    if not is_completed:
        return filename, "no file uploaded", 0

    if filenames is not None:
        if upload_id:
            root_folder = Path(UPLOAD_FOLDER_ROOT) / upload_id
        else:
            root_folder = Path(UPLOAD_FOLDER_ROOT)

        # h5_file = root_folder / filenames[0]
        # hdf5_data, _ = process_uploaded_hdf5(h5_file, filenames[0])
        return filenames[0], basename(filenames[0]), 0

    return filename, "no file uploaded", 0


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
