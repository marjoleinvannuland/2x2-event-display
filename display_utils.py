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
    fig.add_traces(tpc_center)
    fig.add_traces(anodes)
    fig.add_traces(cathodes)

    return fig


def plot_segs(segs, sim_version, **kwargs):
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


def plot_light(this_detector, n_photons, op_indeces, max_integral):
    """Plot optical detectors"""
    COLORSCALE = plotly.colors.make_colorscale(
        plotly.colors.convert_colors_to_same_type(plotly.colors.sequential.YlOrRd)[0]
    )
    drawn_objects = []
    ys = np.flip(
        np.array(
            [
                -595.43,
                -545.68,
                -490.48,
                -440.73,
                -385.53,
                -335.78,
                -283.65,
                -236.65,
                -178.70,
                -131.70,
                -73.75,
                -26.75,
                25.38,
                75.13,
                130.33,
                180.08,
                235.28,
                285.03,
                337.15,
                384.15,
                442.10,
                489.10,
                547.05,
                594.05,
            ]
        )
        / 10
    )
    light_width = ys[1] - ys[0]

    for ix in range(0, this_detector.tpc_borders.shape[0]):
        for ilight, light_y in enumerate(ys):
            for iside in range(2):
                opid = ilight + iside * len(ys) + ix * len(ys) * 2
                if opid not in op_indeces:
                    continue
                xx = np.linspace(
                    this_detector.tpc_borders[ix][2][0],
                    this_detector.tpc_borders[ix][2][1],
                    2,
                )
                zz = np.linspace(
                    light_y - light_width / 2 + this_detector.tpc_offsets[0][1] + 0.25,
                    light_y + light_width / 2 + this_detector.tpc_offsets[0][1] - 0.25,
                    2,
                )

                xx, zz = np.meshgrid(xx, zz)
                light_color = [
                    [
                        0.0,
                        get_continuous_color(
                            COLORSCALE, intermed=max(0, n_photons[opid]) / max_integral
                        ),
                    ],
                    [
                        1.0,
                        get_continuous_color(
                            COLORSCALE, intermed=max(0, n_photons[opid]) / max_integral
                        ),
                    ],
                ]

                if ix % 2 == 0:
                    flip = 0
                else:
                    flip = -1

                opid_str = f"opid_{opid}"
                light_plane = dict(
                    type="surface",
                    y=xx,
                    x=np.full(xx.shape, this_detector.tpc_borders[ix][0][iside + flip]),
                    z=zz,
                    opacity=0.4,
                    hoverinfo="text",
                    ids=[[opid_str, opid_str], [opid_str, opid_str]],
                    text=f"Optical detector {opid} waveform integral<br>{n_photons[opid]:.2e}",
                    colorscale=light_color,
                    showlegend=False,
                    showscale=False,
                )

                drawn_objects.append(light_plane)

    return drawn_objects


def get_continuous_color(colorscale, intermed):
    """
    Plotly continuous colorscales assign colors to the range [0, 1]. This function computes the intermediate
    color for any value in that range.

    Plotly doesn't make the colorscales directly accessible in a common format.
    Some are ready to use:

        colorscale = plotly.colors.PLOTLY_SCALES["Greens"]

    Others are just swatches that need to be constructed into a colorscale:

        viridis_colors, scale = plotly.colors.convert_colors_to_same_type(plotly.colors.sequential.Viridis)
        colorscale = plotly.colors.make_colorscale(viridis_colors, scale=scale)

    :param colorscale: A plotly continuous colorscale defined with RGB string colors.
    :param intermed: value in the range [0, 1]
    :return: color in rgb string format
    :rtype: str
    """
    if len(colorscale) < 1:
        raise ValueError("colorscale must have at least one color")

    if intermed <= 0 or len(colorscale) == 1:
        return colorscale[0][1]
    if intermed >= 1:
        return colorscale[-1][1]

    for cutoff, color in colorscale:
        if intermed > cutoff:
            low_cutoff, low_color = cutoff, color
        if intermed <= cutoff:
            high_cutoff, high_color = cutoff, color
            break

    # noinspection PyUnboundLocalVariable
    return plotly.colors.find_intermediate_color(
        lowcolor=low_color,
        highcolor=high_color,
        intermed=((intermed - low_cutoff) / (high_cutoff - low_cutoff)),
        colortype="rgb",
    )
