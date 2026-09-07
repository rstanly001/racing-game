"""Analysis plots.

The non-interactive Agg backend is selected before pyplot is imported,
because the package is graded on a machine with no display. No figure is
ever shown; every function writes a PNG and returns its path.

Colours are assigned to cars in a fixed order, so a car keeps its colour
across every figure and adding a third car never repaints the first two.
The palette was checked for colour-blind separation rather than chosen by
eye. Speed is a magnitude rather than an identity, so it gets a single-hue
ramp instead of a categorical colour.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # must precede the pyplot import

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, Normalize  # noqa: E402

from racing.exceptions import TelemetryError  # noqa: E402
from racing.telemetry.analysis import (  # noqa: E402
    best_lap_of,
    compare_cars,
    fastest_lap,
    lap_summary,
)

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("output")
FIGURE_DPI = 150
FIGURE_SIZE = (10.0, 5.5)

# One hue per car, in a fixed order. Never cycled: a fifth car would need a
# different treatment rather than a repeated colour.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]

# Speed is a magnitude, so it gets one hue running light to dark. The ramp
# starts part way up so the slowest points are still legible on white.
SPEED_RAMP = LinearSegmentedColormap.from_list(
    "speed", ["#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]
)

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SOFT = "#52514e"
GRID = "#e4e3df"


def _prepare(path: Path | str) -> Path:
    """Resolve an output path and create its parent directory."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _cars(telemetry: pd.DataFrame) -> list[str]:
    """Return the cars in the recording, in a stable order.

    Raises
    ------
    TelemetryError
        If the recording is empty, or holds more cars than the palette has
        colours for.
    """
    names = sorted(telemetry["car"].unique())

    if not names:
        raise TelemetryError("there is no telemetry to plot")

    if len(names) > len(SERIES):
        raise TelemetryError(
            f"the palette holds {len(SERIES)} cars, and this race had {len(names)}"
        )

    return names


def _colour(cars: list[str], car: str) -> str:
    """Return the fixed colour for one car."""
    return SERIES[cars.index(car)]


def _style(axes: plt.Axes, title: str, xlabel: str, ylabel: str) -> None:
    """Apply the shared look: a recessive grid, and no box around the plot."""
    axes.set_title(title, color=INK, fontsize=12, loc="left", pad=12)
    axes.set_xlabel(xlabel, color=INK_SOFT, fontsize=10)
    axes.set_ylabel(ylabel, color=INK_SOFT, fontsize=10)
    axes.grid(True, color=GRID, linewidth=0.8)
    axes.set_axisbelow(True)
    axes.tick_params(colors=INK_SOFT, labelsize=9)

    for edge in ("top", "right"):
        axes.spines[edge].set_visible(False)
    for edge in ("left", "bottom"):
        axes.spines[edge].set_color(GRID)


def _figure(*args: object, **kwargs: object) -> tuple[plt.Figure, object]:
    """Return a figure and axes already painted the surface colour."""
    figure, axes = plt.subplots(*args, **kwargs)
    figure.patch.set_facecolor(SURFACE)

    for one in np.atleast_1d(axes).ravel():
        one.set_facecolor(SURFACE)

    return figure, axes


def _save(figure: plt.Figure, path: Path) -> Path:
    """Write a figure out and close it, so nothing is ever displayed."""
    figure.tight_layout()
    figure.savefig(path, dpi=FIGURE_DPI, facecolor=SURFACE)
    plt.close(figure)
    logger.info("wrote %s", path)
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
    path = _prepare(output_path)
    speeds = compare_cars(telemetry)
    cars = _cars(telemetry)

    figure, axes = _figure(figsize=FIGURE_SIZE)

    for car in speeds.columns:
        axes.plot(
            speeds.index,
            speeds[car],
            color=_colour(cars, car),
            linewidth=2.0,
            label=car,
        )

    _style(
        axes,
        "Speed on each car's best lap",
        "Distance around the lap (px)",
        "Speed (px/s)",
    )
    axes.legend(frameon=False, labelcolor=INK_SOFT, fontsize=9, loc="lower right")
    return _save(figure, path)


def plot_racing_line(
    telemetry: pd.DataFrame,
    output_path: Path | str = DEFAULT_OUTPUT_DIR / "racing_line.png",
) -> Path:
    """Plot the path each car actually drove, coloured by speed.

    One panel per car, sharing a single speed scale. Putting both cars on
    one panel would need colour to carry identity and magnitude at once,
    and it can only do one of them.
    """
    path = _prepare(output_path)
    cars = _cars(telemetry)
    laps = {car: best_lap_of(telemetry, car) for car in cars}

    # Scale the colour to the laps actually drawn. Taking the range from the
    # whole recording would include the standing start, and a lap that never
    # drops below 240 would then render as one flat shade.
    speeds = pd.concat([lap["speed"] for lap in laps.values()])
    scale = Normalize(speeds.min(), speeds.max())

    size = (5.6 * len(cars), 4.4)
    figure, panels = _figure(1, len(cars), figsize=size, squeeze=False)

    for panel, car in zip(panels[0], cars, strict=True):
        lap = laps[car]
        points = np.column_stack([lap["x"], lap["y"]]).reshape(-1, 1, 2)

        trace = LineCollection(
            np.concatenate([points[:-1], points[1:]], axis=1),
            cmap=SPEED_RAMP,
            norm=scale,
            linewidth=3.0,
        )
        trace.set_array(lap["speed"].to_numpy()[:-1])
        panel.add_collection(trace)

        panel.set_xlim(lap["x"].min() - 40, lap["x"].max() + 40)
        panel.set_ylim(lap["y"].max() + 40, lap["y"].min() - 40)  # screen y grows down
        panel.set_aspect("equal")
        _style(panel, f"{car} — best lap", "x (px)", "y (px)")

    bar = figure.colorbar(trace, ax=panels[0], fraction=0.03, pad=0.02)
    bar.set_label("Speed (px/s)", color=INK_SOFT, fontsize=10)
    bar.ax.tick_params(colors=INK_SOFT, labelsize=9)
    bar.outline.set_visible(False)

    figure.savefig(path, dpi=FIGURE_DPI, facecolor=SURFACE)
    plt.close(figure)
    logger.info("wrote %s", path)
    return path


def plot_lap_times(
    telemetry: pd.DataFrame,
    output_path: Path | str = DEFAULT_OUTPUT_DIR / "lap_times.png",
) -> Path:
    """Plot lap time against lap number, one line per car."""
    path = _prepare(output_path)
    laps = lap_summary(telemetry)
    cars = _cars(telemetry)

    figure, axes = _figure(figsize=FIGURE_SIZE)

    for car in cars:
        times = laps.loc[car, "lap_time"]
        axes.plot(
            times.index,
            times.to_numpy(),
            color=_colour(cars, car),
            linewidth=2.0,
            marker="o",
            markersize=8,
            markeredgecolor=SURFACE,
            markeredgewidth=2,
            label=car,
        )

        # Only the quickest lap is labelled: a number on every point is noise.
        axes.annotate(
            f"{car} best {times.min():.2f}s",
            xy=(times.idxmin(), times.min()),
            xytext=(0, -20),
            textcoords="offset points",
            color=INK_SOFT,
            fontsize=9,
            ha="center",
        )

    _style(axes, "Lap times", "Lap", "Lap time (s)")
    axes.set_xticks(sorted(set(laps.index.get_level_values("lap"))))
    axes.legend(frameon=False, labelcolor=INK_SOFT, fontsize=9)
    return _save(figure, path)


def plot_inputs(
    telemetry: pd.DataFrame,
    output_path: Path | str = DEFAULT_OUTPUT_DIR / "inputs.png",
) -> Path:
    """Plot throttle, brake, and steering over the race's fastest lap.

    Three stacked panels sharing an x-axis of lap distance. They are not
    overlaid on one pair of axes: steering runs from -1 to 1 and the pedals
    from 0 to 1, and a second y-scale would make the three look comparable
    when they are not.
    """
    path = _prepare(output_path)
    lap = fastest_lap(telemetry).sort_values("lap_distance")
    car = str(lap["car"].iloc[0])
    colour = _colour(_cars(telemetry), car)

    figure, panels = _figure(3, 1, figsize=(10.0, 7.0), sharex=True)
    traces = [
        ("throttle", "Throttle", (0.0, 1.05)),
        ("brake", "Brake", (0.0, 1.05)),
        ("steering", "Steering", (-1.1, 1.1)),
    ]

    for panel, (column, label, limits) in zip(panels, traces, strict=True):
        panel.fill_between(
            lap["lap_distance"], lap[column], color=colour, alpha=0.25, linewidth=0
        )
        panel.plot(lap["lap_distance"], lap[column], color=colour, linewidth=2.0)
        panel.set_ylim(*limits)
        _style(panel, "", "", label)

    panels[0].set_title(
        f"Driver inputs — {car}, fastest lap of the race",
        color=INK,
        fontsize=12,
        loc="left",
        pad=12,
    )
    panels[-1].set_xlabel("Distance around the lap (px)", color=INK_SOFT, fontsize=10)
    return _save(figure, path)


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
