"""Telemetry analysis with pandas.

Every function takes the telemetry DataFrame and returns a summary frame, so
the same code serves the CLI, the notebook, and the plotting module.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def lap_summary(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Return per-car, per-lap statistics.

    Parameters
    ----------
    telemetry
        A telemetry frame as produced by :meth:`Telemetry.to_frame`.

    Returns
    -------
    pandas.DataFrame
        Indexed by car and lap, with lap time, average and top speed, time
        spent on throttle and on the brakes, and collision count.
    """
    # TODO: implement with groupby(["car", "lap"]).agg(...)
    raise NotImplementedError


def race_summary(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Return one row per car: total time, best lap, top speed, collisions."""
    # TODO: implement
    raise NotImplementedError


def sector_times(telemetry: pd.DataFrame, n_sectors: int = 3) -> pd.DataFrame:
    """Split each lap into equal sectors by distance and time each one.

    Parameters
    ----------
    telemetry
        The telemetry frame.
    n_sectors
        How many sectors to divide each lap into.

    Returns
    -------
    pandas.DataFrame
        Indexed by car, lap, and sector.
    """
    # TODO: implement with pd.cut on lap_distance
    raise NotImplementedError


def fastest_lap(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Return the telemetry rows belonging to the fastest lap of the race."""
    # TODO: implement
    raise NotImplementedError


def compare_cars(telemetry: pd.DataFrame) -> pd.DataFrame:
    """Return each car's speed on its best lap, aligned by lap distance.

    Aligning by distance rather than time is what makes the two traces
    directly comparable: the same x value is the same point on the circuit
    for both cars.
    """
    # TODO: implement by interpolating both cars onto a common distance grid
    raise NotImplementedError
