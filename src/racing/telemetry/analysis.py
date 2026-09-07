"""Telemetry analysis with pandas.

Every function takes the telemetry DataFrame and returns a summary frame, so
the same code serves the CLI, the notebook, and the plotting module.

A row's ``lap`` column counts laps *completed*, so the rows driven during
the opening lap carry a zero. Everything here works on a one-based lap
number instead, and the trailing group — the laps a car is credited with
after it has finished, while it waits for the rest of the field — falls out
naturally, because there is no following crossing to measure it against.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from racing.exceptions import TelemetryError

logger = logging.getLogger(__name__)

# How many points each car's trace is resampled onto when two cars are
# compared over a lap.
COMPARISON_POINTS = 400


def _numbered(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Return the telemetry with laps numbered from one rather than zero."""
    if telemetry.empty:
        raise TelemetryError("there is no telemetry to analyse")

    return telemetry.assign(lap=telemetry["lap"] + 1)


def _timestep(telemetry: pd.DataFrame) -> float:
    """Return the interval between telemetry frames, read off the data."""
    times = np.unique(telemetry["time"].to_numpy())
    if times.size < 2:
        raise TelemetryError("telemetry needs at least two frames to time anything")

    return float(np.median(np.diff(times)))


def lap_summary(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Return per-car, per-lap statistics.

    Lap time is measured from one start-line crossing to the next, taken as
    the gap between the first frame of consecutive laps. A lap with no
    following crossing has not been completed, and is dropped.

    Parameters
    ----------
    telemetry
        A telemetry frame as produced by :meth:`Telemetry.to_frame`.

    Returns
    -------
    pandas.DataFrame
        Indexed by car and lap, with lap time, average and top speed, time
        spent on throttle and on the brakes, and collision count.

    Raises
    ------
    TelemetryError
        If the frame is empty.
    """
    frame = _numbered(telemetry)

    started = frame.groupby(["car", "lap"])["time"].min()
    lap_time = started.groupby(level="car").shift(-1) - started

    summary = frame.groupby(["car", "lap"]).agg(
        average_speed=("speed", "mean"),
        top_speed=("speed", "max"),
        throttle_share=("throttle", "mean"),
        brake_share=("brake", "mean"),
        contacts=("collision", "sum"),
    )
    summary.insert(0, "lap_time", lap_time)
    summary = summary.dropna(subset=["lap_time"])

    summary["on_throttle"] = summary["throttle_share"] * summary["lap_time"]
    summary["on_brakes"] = summary["brake_share"] * summary["lap_time"]

    return summary.drop(columns=["throttle_share", "brake_share"])


def race_summary(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Return one row per car: total time, best lap, top speed, collisions.

    Parameters
    ----------
    telemetry
        A telemetry frame.

    Returns
    -------
    pandas.DataFrame
        Indexed by car, ordered by total time, quickest first.
    """
    laps = lap_summary(telemetry)

    summary = laps.groupby(level="car").agg(
        laps=("lap_time", "size"),
        total_time=("lap_time", "sum"),
        best_lap=("lap_time", "min"),
        average_lap=("lap_time", "mean"),
        top_speed=("top_speed", "max"),
        contacts=("contacts", "sum"),
    )
    return summary.sort_values("total_time")


def sector_times(telemetry: pd.DataFrame, n_sectors: int = 3) -> pd.DataFrame:
    """Split each lap into equal sectors by distance and time each one.

    Sectors are cut by distance around the lap rather than by time, so the
    same sector is the same piece of tarmac for every car and every lap.

    Each sector is timed by counting the frames spent in it, not by taking
    the span between its first and last. A car starts the race behind the
    line, so its opening lap enters the final sector twice — once on the
    grid and once on the way past — and a first-to-last span would swallow
    almost the whole lap.

    Parameters
    ----------
    telemetry
        The telemetry frame.
    n_sectors
        How many sectors to divide each lap into.

    Returns
    -------
    pandas.DataFrame
        Indexed by car, lap, and sector, with the time spent in each and the
        average speed through it.

    Raises
    ------
    TelemetryError
        If the frame is empty or ``n_sectors`` is not positive.
    """
    if n_sectors < 1:
        raise TelemetryError(f"a lap needs at least one sector, got {n_sectors}")

    frame = _numbered(telemetry)
    edges = np.linspace(0.0, frame["lap_distance"].max(), n_sectors + 1)

    frame = frame.assign(
        sector=pd.cut(
            frame["lap_distance"],
            bins=edges,
            labels=range(1, n_sectors + 1),
            include_lowest=True,
        )
    )

    grouped = frame.groupby(["car", "lap", "sector"], observed=True)
    sectors = grouped.agg(
        frames=("time", "size"),
        average_speed=("speed", "mean"),
    )
    sectors.insert(0, "sector_time", sectors.pop("frames") * _timestep(frame))

    # Drop the trailing laps a car is credited with after finishing.
    completed = lap_summary(telemetry).index
    return sectors[sectors.index.droplevel("sector").isin(completed)]


def fastest_lap(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Return the telemetry rows belonging to the fastest lap of the race.

    Returns
    -------
    pandas.DataFrame
        Every frame of that one lap, in order, with its car and lap number
        intact so the caller knows whose it was.
    """
    laps = lap_summary(telemetry)
    car, lap = laps["lap_time"].idxmin()
    logger.debug("fastest lap: %s on lap %d", car, lap)

    frame = _numbered(telemetry)
    return frame[(frame["car"] == car) & (frame["lap"] == lap)].reset_index(drop=True)


def best_lap_of(telemetry: pd.DataFrame, car: str) -> pd.DataFrame:
    """Return every frame of one car's quickest lap."""
    laps = lap_summary(telemetry)

    if car not in laps.index.get_level_values("car"):
        raise TelemetryError(f"no completed laps for {car!r}")

    lap = laps.loc[car, "lap_time"].idxmin()
    frame = _numbered(telemetry)
    return frame[(frame["car"] == car) & (frame["lap"] == lap)]


def compare_cars(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Return each car's speed on its best lap, aligned by lap distance.

    Aligning by distance rather than time is what makes the two traces
    directly comparable: the same x value is the same point on the circuit
    for both cars.

    Returns
    -------
    pandas.DataFrame
        Indexed by distance around the lap, one column of speed per car.
    """
    frame = _numbered(telemetry)
    grid = np.linspace(0.0, frame["lap_distance"].max(), COMPARISON_POINTS)

    speeds = {}
    for car in sorted(frame["car"].unique()):
        lap = best_lap_of(telemetry, car).sort_values("lap_distance")
        speeds[car] = np.interp(grid, lap["lap_distance"], lap["speed"])

    return pd.DataFrame(speeds, index=pd.Index(grid, name="lap_distance"))
