"""Procedural track generation.

Building circuits from parameters rather than hard-coding coordinates means
new tracks cost one line, and the generator itself is a natural place for
numpy work.
"""

from __future__ import annotations

import numpy as np

from racing.track.track import Track

# How tall a figure-eight is next to its width. The bare curve is half as
# tall as it is wide, which leaves the two loops too tight to drive.
HEIGHT_RATIO = 0.62


def build_oval(
    name: str = "Oval",
    centre: tuple[float, float] = (640.0, 360.0),
    radius_x: float = 440.0,
    radius_y: float = 240.0,
    n_points: int = 180,
    width: float = 120.0,
) -> Track:
    """Generate a simple elliptical circuit.

    Parameters
    ----------
    name
        Display name.
    centre
        Centre of the ellipse.
    radius_x, radius_y
        Semi-axes in pixels.
    n_points
        Number of centre-line nodes. More gives smoother boundaries.
    width
        Track width in pixels.

    Returns
    -------
    Track
        The generated circuit.

    Examples
    --------
    >>> track = build_oval(radius_x=200.0, radius_y=100.0)
    >>> len(track)
    180
    """
    # The last angle stops short of a full turn, so the closing segment back
    # to the first node is the same length as every other one.
    angles = np.linspace(0.0, 2 * np.pi, n_points, endpoint=False)
    centre_line = np.column_stack(
        [
            centre[0] + radius_x * np.cos(angles),
            centre[1] + radius_y * np.sin(angles),
        ]
    )
    return Track(name=name, centre_line=centre_line, width=width)


def build_figure_eight(
    name: str = "Figure Eight",
    centre: tuple[float, float] = (640.0, 360.0),
    scale: float = 380.0,
    n_points: int = 240,
    width: float = 110.0,
) -> Track:
    """Generate a figure-of-eight circuit from a lemniscate curve.

    The lemniscate of Gerono, ``x = cos t`` and ``y = sin t cos t``, is a
    closed loop that crosses itself once, which the renderer handles because
    the track surface is laid down segment by segment rather than as one
    filled polygon.

    Parameters
    ----------
    name
        Display name.
    centre
        Centre of the figure.
    scale
        Half the overall width, in pixels.
    n_points
        Number of centre-line nodes.
    width
        Track width in pixels.

    Returns
    -------
    Track
        The generated circuit.
    """
    angles = np.linspace(0.0, 2 * np.pi, n_points, endpoint=False)
    centre_line = np.column_stack(
        [
            centre[0] + scale * np.cos(angles),
            centre[1] + 2 * scale * HEIGHT_RATIO * np.sin(angles) * np.cos(angles),
        ]
    )
    return Track(name=name, centre_line=centre_line, width=width)


BUILDERS = {
    "oval": build_oval,
    "figure_eight": build_figure_eight,
}
