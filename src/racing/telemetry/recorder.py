"""Per-frame telemetry recording.

Every physics step, one row per car is appended. At the end of a race the
whole recording becomes a :class:`pandas.DataFrame`, which is what the
analysis and plotting modules consume.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from racing.entities.vehicle import Vehicle

logger = logging.getLogger(__name__)

COLUMNS = [
    "time",
    "car",
    "lap",
    "x",
    "y",
    "heading",
    "speed",
    "throttle",
    "brake",
    "steering",
    "lap_distance",
    "collision",
]


class Telemetry:
    """Records the state of every car on every physics step.

    Rows are accumulated in a plain list and converted to a DataFrame only
    once, at the end of the race. Appending to a DataFrame per frame would
    be far slower.

    Examples
    --------
    >>> telemetry = Telemetry()
    >>> telemetry.record(0.0, car, lap_distance=120.0, collision=False)
    >>> df = telemetry.to_frame()
    """

    def __init__(self) -> None:
        self._rows: list[dict[str, float | str | int | bool]] = []

    def record(
        self,
        time: float,
        vehicle: Vehicle,
        lap_distance: float,
        collision: bool = False,
    ) -> None:
        """Append one row for one car at one instant.

        Parameters
        ----------
        time
            Race time in seconds.
        vehicle
            The car whose state is being recorded.
        lap_distance
            How far around the lap the car is, in pixels.
        collision
            Whether a collision occurred on this step.
        """
        # TODO: implement
        raise NotImplementedError

    def to_frame(self) -> pd.DataFrame:
        """Return the recording as a DataFrame with :data:`COLUMNS`."""
        # TODO: implement
        raise NotImplementedError

    def to_csv(self, path: Path | str) -> Path:
        """Write the recording to CSV and return the path."""
        # TODO: implement, creating the parent directory if needed
        raise NotImplementedError

    @classmethod
    def from_csv(cls, path: Path | str) -> pd.DataFrame:
        """Read a saved recording back, for the ``analyze`` command.

        Raises
        ------
        TelemetryError
            If the file is missing or lacks the expected columns.
        """
        # TODO: implement
        raise NotImplementedError

    def __len__(self) -> int:
        """Return the number of recorded rows."""
        return len(self._rows)

    def __repr__(self) -> str:
        """Return the number of rows recorded so far."""
        return f"<Telemetry rows={len(self)}>"
