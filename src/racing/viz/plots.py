"""Analysis plots.

The non-interactive Agg backend is selected before pyplot is imported,
because the package is graded on a machine with no display. No figure is
ever shown; every function writes a PNG and returns its path.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # must precede the pyplot import

import matplotlib.pyplot as plt  # noqa: E402, F401  (used once plots are implemented)
import pandas as pd  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("output")
FIGURE_DPI = 150


def _prepare(path: Path | str) -> Path:
    """Resolve an output path and create its parent directory."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def plot_speed_trace(
    telemetry: pd.DataFrame,
    output_path: Path | str = DEFAULT_OUTPUT_DIR / "speed_trace.png",
) -> Path:
    """Plot both cars' speed against lap distance on their best laps.

    Because the x-axis is distance rather than time, the two traces line up
    corner for corner, which is exactly how real race engineers compare
    drivers.

    Returns
    -------
    pathlib.Path
        The path the figure was written to.
    """
    # TODO: implement, then fig.savefig(path, dpi=FIGURE_DPI); plt.close(fig)
    raise NotImplementedError


def plot_racing_line(
    telemetry: pd.DataFrame,
    output_path: Path | str = DEFAULT_OUTPUT_DIR / "racing_line.png",
) -> Path:
    """Plot the path each car actually drove, coloured by speed.

    Uses a scatter of x against y with speed as the colour channel, which
    makes braking zones and apexes immediately visible.
    """
    # TODO: implement
    raise NotImplementedError


def plot_lap_times(
    telemetry: pd.DataFrame,
    output_path: Path | str = DEFAULT_OUTPUT_DIR / "lap_times.png",
) -> Path:
    """Plot lap time against lap number, one line per car."""
    # TODO: implement
    raise NotImplementedError


def plot_inputs(
    telemetry: pd.DataFrame,
    output_path: Path | str = DEFAULT_OUTPUT_DIR / "inputs.png",
) -> Path:
    """Plot throttle, brake, and steering traces over one lap.

    Three stacked subplots sharing an x-axis of lap distance.
    """
    # TODO: implement with plt.subplots(3, 1, sharex=True)
    raise NotImplementedError


def plot_all(
    telemetry: pd.DataFrame,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> list[Path]:
    """Generate every figure and return the list of paths written."""
    output_dir = Path(output_dir)
    return [
        plot_speed_trace(telemetry, output_dir / "speed_trace.png"),
        plot_racing_line(telemetry, output_dir / "racing_line.png"),
        plot_lap_times(telemetry, output_dir / "lap_times.png"),
        plot_inputs(telemetry, output_dir / "inputs.png"),
    ]
