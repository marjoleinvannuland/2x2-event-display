"""
Utility functions for displaying data in the app
"""
import h5flow
import numpy as np
import plotly.graph_objects as go

def parse_contents(filename):
    data = h5flow.data.H5FlowDataManager(filename, "r")
    num_events = data["charge/events/data"].shape[0]
    return data, num_events

    
def create_3d_figure(data, evid):
    fig = go.Figure()
    # Select the hits for the current event
    prompthits_ev = data["charge/events", "charge/calib_prompt_hits", evid]
    finalhits_ev = data["charge/events", "charge/calib_final_hits", evid]
    # select the segments (truth) for the current event
    try:
        prompthits_segs = data[
            "charge/events",
            "charge/calib_prompt_hits",
            "charge/packets",
            "mc_truth/segments",  # called segments in minirun4
            evid,
        ]
        print("Found truth info in minirun4 format")
    except:
        print("No truth info in minirun4 format found")
        try:
            prompthits_segs = data[
                "charge/events",
                "charge/calib_prompt_hits",
                "charge/packets",
                "mc_truth/tracks",  # called tracks in minirun3
                evid,
            ]
            print("Found truth info in minirun3 format")
        except:
            print("No truth info in minirun3 format found")
            prompthits_segs = None

    # Plot the prompt hits
    prompthits_traces = go.Scatter3d(
        x=prompthits_ev.data["x"].flatten(),
        y=(prompthits_ev.data["z"].flatten()), # swap y and z
        z=(prompthits_ev.data["y"].flatten()),
        marker_color=prompthits_ev.data["E"].flatten() * 1000,  # convert to MeV?
        marker={
            "size": 1.75,
            "opacity": 0.7,
            "colorscale": "cividis",
            "colorbar": {
                "title": "Hit energy [MeV]",
                "titlefont": {"size": 12},
                "tickfont": {"size": 10},
                "thickness": 15,
                "len": 0.5,
                "xanchor": "left",
                "x": 0,
            },
        },
        name="prompt hits",
        mode="markers",
        showlegend=True,
        opacity=0.7,
        customdata=prompthits_ev.data["E"].flatten() * 1000,
        hovertemplate="<b>x:%{x:.3f}</b><br>y:%{y:.3f}<br>z:%{z:.3f}<br>E:%{customdata:.3f}",
    )
    fig.add_traces(prompthits_traces)

    # Plot the final hits
    finalhits_traces = go.Scatter3d(
        x=finalhits_ev.data["x"].flatten(),
        y=(finalhits_ev.data["z"].flatten()), # swap y and z
        z=(finalhits_ev.data["y"].flatten()),
        marker_color=finalhits_ev.data["E"].flatten() * 1000,
        marker={
            "size": 1.75,
            "opacity": 0.7,
            "colorscale": "Plasma",
            "colorbar": {
                "title": "Hit energy [MeV]",
                "titlefont": {"size": 12},
                "tickfont": {"size": 10},
                "thickness": 15,
                "len": 0.5,
                "xanchor": "left",
                "x": 0,
            },
        },
        name="final hits",
        mode="markers",
        visible="legendonly",
        showlegend=True,
        opacity=0.7,
        customdata=finalhits_ev.data["E"].flatten() * 1000,
        hovertemplate="<b>x:%{x:.3f}</b><br>y:%{y:.3f}<br>z:%{z:.3f}<br>E:%{customdata:.3f}",
    )
    fig.add_traces(finalhits_traces)

    if prompthits_segs is not None:
        segs_traces = plot_segs(
            prompthits_segs[0, :, 0, 0],
            mode="lines",
            name="edep segments",
            visible="legendonly",
            line_color="red",
            showlegend=True,
        )
        fig.add_traces(segs_traces)
    
    return fig

def plot_segs(segs, **kwargs):
    def to_list(axis):
        return (
            np.column_stack(
                [segs[f"{axis}_start"], segs[f"{axis}_end"], np.full(len(segs), None)]
            ) # multiply by ten for minirun3 for some reason
            .flatten()
            .tolist()
        )

    x, y, z = (to_list(axis) for axis in "xyz")
    trace = go.Scatter3d(x=x, y=z, z=y, **kwargs) # swap y and z

    return trace