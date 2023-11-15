"""
Utility functions for displaying data in the app
"""
import h5flow
import numpy as np
import plotly
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
        sim_version = "minirun4"
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
            sim_version = "minirun3"
            print("Found truth info in minirun3 format")
        except:
            print("No truth info in minirun3 format found")
            prompthits_segs = None

    # Plot the prompt hits
    prompthits_traces = go.Scatter3d(
        x=prompthits_ev.data["x"].flatten(),
        y=(prompthits_ev.data["y"].flatten()),
        z=(prompthits_ev.data["z"].flatten()),
        marker_color=prompthits_ev.data["E"].flatten()
        * 1000,  # convert to MeV from GeV for minirun4, not sure for minirun3
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
        y=(finalhits_ev.data["y"].flatten()),
        z=(finalhits_ev.data["z"].flatten()),
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
            sim_version=sim_version,
            mode="lines",
            name="edep segments",
            visible="legendonly",
            line_color="red",
            showlegend=True,
        )
        fig.add_traces(segs_traces)

    # Draw the TPC
    tpc_center, anodes, cathodes = draw_tpc(sim_version)
    light_detectors = draw_light_detectors() # this doesn't do anything yet
    
    fig.add_traces(tpc_center)
    fig.add_traces(anodes)
    fig.add_traces(cathodes)
    fig.add_traces(light_detectors) # not implemented yet

    return fig


def plot_segs(segs, sim_version="minirun4", **kwargs):
    def to_list(axis):
        if sim_version == "minirun4":
            nice_array = np.column_stack(
                [segs[f"{axis}_start"], segs[f"{axis}_end"], np.full(len(segs), None)]
            ).flatten()
        if sim_version == "minirun3":
            nice_array = np.column_stack(
                [
                    segs[f"{axis}_start"] * 10,
                    segs[f"{axis}_end"] * 10,
                    np.full(len(segs), None),
                ]
            ).flatten()
        return nice_array

    x, y, z = (to_list(axis) for axis in "xyz")

    trace = go.Scatter3d(x=x, y=y, z=z, **kwargs)

    return trace


def draw_tpc(sim_version="minirun4"):
    anode_xs = np.array([-63.931, -3.069, 3.069, 63.931])
    anode_ys = np.array([-19.8543, 103.8543])  # two ys
    anode_zs = np.array([-64.3163, -2.6837, 2.6837, 64.3163])  # four zs
    if sim_version == "minirun4":  # hit coordinates are in cm
        detector_center = (0, -268, 1300)
        anode_ys = anode_ys - (268 + 42)
        anode_zs = anode_zs + 1300
    if sim_version == "minirun3":  # hit coordinates are in mm
        detector_center = (0, 42 * 10, 0)
        anode_xs = anode_xs * 10
        anode_ys = anode_ys * 10
        anode_zs = anode_zs * 10

    center = go.Scatter3d(
        x=[detector_center[0]],
        y=[detector_center[1]],
        z=[detector_center[2]],
        marker=dict(size=3, color="green", opacity=0.5),
        mode="markers",
        name="tpc center",
    )
    anodes = draw_anode_planes(
        anode_xs, anode_ys, anode_zs, colorscale="ice", showscale=False, opacity=0.1
    )
    cathodes = draw_cathode_planes(
        anode_xs, anode_ys, anode_zs, colorscale="burg", showscale=False, opacity=0.1
    )
    return center, anodes, cathodes


def draw_cathode_planes(x_boundaries, y_boundaries, z_boundaries, **kwargs):
    traces = []
    for i_z in range(int(len(z_boundaries) / 2)):
        for i_x in range(int(len(x_boundaries) / 2)):
            z, y = np.meshgrid(
                np.linspace(z_boundaries[i_z * 2], z_boundaries[i_z * 2 + 1], 2),
                np.linspace(y_boundaries.min(), y_boundaries.max(), 2),
            )
            x = (
                (x_boundaries[i_x * 2] + x_boundaries[i_x * 2 + 1])
                * 0.5
                * np.ones(z.shape)
            )
            traces.append(go.Surface(x=x, y=y, z=z, **kwargs))

    return traces


def draw_anode_planes(x_boundaries, y_boundaries, z_boundaries, **kwargs):
    traces = []
    for i_z in range(int(len(z_boundaries) / 2)):
        for i_x in range(int(len(x_boundaries))):
            z, y = np.meshgrid(
                np.linspace(z_boundaries[i_z * 2], z_boundaries[i_z * 2 + 1], 2),
                np.linspace(y_boundaries.min(), y_boundaries.max(), 2),
            )
            x = x_boundaries[i_x] * np.ones(z.shape)

            traces.append(go.Surface(x=x, y=y, z=z, **kwargs))

    return traces

def draw_light_detectors(data):
    try:
        data["/light/"]
    except:
        print("No light information found, not plotting light detectors")
    return []