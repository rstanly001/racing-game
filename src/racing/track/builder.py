"""Procedural track generation.

Building circuits from parameters rather than hard-coding coordinates means
new tracks cost one line, and the generator itself is a natural place for
numpy work.
"""

from __future__ import annotations

import numpy as np  # noqa: F401  (used once the builders are implemented)

from racing.track.track import Track


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
    """
    # TODO: implement with np.linspace over [0, 2*pi) and cos/sin
    raise NotImplementedError


def build_figure_eight(
    name: str = "Figure Eight",
    centre: tuple[float, float] = (640.0, 360.0),
    scale: float = 380.0,
    n_points: int = 240,
    width: float = 110.0,
) -> Track:
    """Generate a figure-of-eight circuit from a lemniscate curve."""
    # TODO: implement with the parametric lemniscate of Gerono
    raise NotImplementedError


def build_random(
    seed: int | None = None,
    n_control: int = 8,
    n_points: int = 240,
    width: float = 120.0,
) -> Track:
    """Generate a random closed circuit.

    Places control points around a circle with randomised radii, then
    smooths them into a closed loop.

    Parameters
    ----------
    seed
        Seed for reproducibility.
    n_control
        Number of control points before smoothing.
    n_points
        Number of nodes in the final centre line.
    width
        Track width in pixels.
    """
    # TODO: implement with np.random.default_rng(seed)
    raise NotImplementedError


BUILDERS = {
    "oval": build_oval,
    "figure_eight": build_figure_eight,
    "random": build_random,
}
