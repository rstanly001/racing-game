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

from racing.exceptions import TelemetryError

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
        self._rows.append(
            {
                "time": time,
                "car": vehicle.name,
                "lap": vehicle.lap,
                "x": float(vehicle.position[0]),
                "y": float(vehicle.position[1]),
                "heading": vehicle.heading,
                "speed": vehicle.speed,
                "throttle": vehicle.throttle,
                "brake": vehicle.brake,
                "steering": vehicle.steering,
                "lap_distance": lap_distance,
                "collision": collision,
            }
        )

    def to_frame(self) -> pd.DataFrame:
        """Return the recording as a DataFrame with :data:`COLUMNS`.

        An empty recording still comes back with the right columns, so
        callers can rely on the shape without checking the length first.
        """
        return pd.DataFrame(self._rows, columns=COLUMNS)

    def to_csv(self, path: Path | str) -> Path:
        """Write the recording to CSV and return the path.

        Parameters
        ----------
        path
            Destination file. Missing parent directories are created.

        Returns
        -------
        pathlib.Path
            The path written to.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_frame().to_csv(path, index=False)
        logger.info("wrote %d telemetry rows to %s", len(self), path)
        return path

    @classmethod
    def from_csv(cls, path: Path | str) -> pd.DataFrame:
        """Read a saved recording back, for the ``analyze`` command.

        Parameters
        ----------
        path
            A CSV written by :meth:`to_csv`.

        Returns
        -------
        pandas.DataFrame
            The recording, with the columns in :data:`COLUMNS`.

        Raises
        ------
        TelemetryError
            If the file is missing or lacks the expected columns.
        """
        path = Path(path)

        try:
            frame = pd.read_csv(path)
        except FileNotFoundError as exc:
            raise TelemetryError(f"no telemetry file at {path}") from exc
        except pd.errors.ParserError as exc:
            raise TelemetryError(f"{path} is not readable as CSV: {exc}") from exc

        missing = [column for column in COLUMNS if column not in frame.columns]
        if missing:
            raise TelemetryError(f"{path} is missing columns: {', '.join(missing)}")

        return frame[COLUMNS]

    def __len__(self) -> int:
        """Return the number of recorded rows."""
        return len(self._rows)

    def __repr__(self) -> str:
        """Return the number of rows recorded so far."""
        return f"<Telemetry rows={len(self)}>"
