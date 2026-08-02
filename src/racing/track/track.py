"""Track geometry, checkpoints, and the racing line."""

from __future__ import annotations

import json  # noqa: F401  (used once load/save are implemented)
import logging
from collections.abc import Iterator
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class Track:
    """A closed circuit defined by a centre line and a width.

    The outer and inner boundaries are derived by offsetting the centre line
    perpendicular to its direction of travel, so a track is fully described
    by a list of points and one width value.

    Parameters
    ----------
    name
        Display name of the circuit.
    centre_line
        Array of shape ``(n, 2)`` giving the centre line, in order, closed
        implicitly (the last point connects back to the first).
    width
        Track width in pixels.
    n_checkpoints
        How many checkpoints to place evenly around the lap. Lap counting
        requires them to be crossed in order.
    """

    def __init__(
        self,
        name: str,
        centre_line: np.ndarray,
        width: float = 120.0,
        n_checkpoints: int = 12,
    ) -> None:
        self.name = name
        self.centre_line = np.asarray(centre_line, dtype=float)
        self.width = float(width)
        self.n_checkpoints = n_checkpoints

    @classmethod
    def load(cls, path: Path | str) -> Track:
        """Load a track from a JSON file.

        Parameters
        ----------
        path
            Path to the track definition.

        Returns
        -------
        Track
            The loaded circuit.

        Raises
        ------
        TrackError
            If the file is missing or does not contain a valid definition.
        """
        # TODO: implement, wrapping json and key errors in TrackError
        raise NotImplementedError

    def save(self, path: Path | str) -> Path:
        """Write this track to a JSON file and return the path."""
        # TODO: implement
        raise NotImplementedError

    @property
    def checkpoints(self) -> np.ndarray:
        """Return checkpoint positions, evenly spaced along the centre line."""
        # TODO: implement
        raise NotImplementedError

    @property
    def start_position(self) -> np.ndarray:
        """Return the position of the start/finish line."""
        return self.centre_line[0]

    @property
    def start_heading(self) -> float:
        """Return the heading a car should start with, in degrees."""
        # TODO: implement from the direction of the first centre-line segment
        raise NotImplementedError

    def racing_line(self) -> np.ndarray:
        """Return a smoothed line the AI aims to follow.

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n, 2)``. A simple implementation returns the
            centre line; a better one pulls the line toward the inside of
            corners and out again on exit.
        """
        # TODO: implement
        raise NotImplementedError

    def distance_from_centre(self, point: np.ndarray) -> float:
        """Return the shortest distance from ``point`` to the centre line."""
        # TODO: implement with a vectorised distance to every segment
        raise NotImplementedError

    def contains(self, point: np.ndarray) -> bool:
        """Return whether ``point`` lies within the track surface."""
        return self.distance_from_centre(point) <= self.width / 2

    def nearest_index(self, point: np.ndarray) -> int:
        """Return the index of the closest centre-line node to ``point``."""
        deltas = self.centre_line - np.asarray(point, dtype=float)
        return int(np.argmin(np.einsum("ij,ij->i", deltas, deltas)))

    def lap_distance(self, point: np.ndarray) -> float:
        """Return how far around the lap ``point`` is, in pixels.

        Used as the x-axis of the speed-trace plot, so two cars can be
        compared at the same point on the circuit rather than at the same
        moment in time.
        """
        # TODO: implement
        raise NotImplementedError

    def __len__(self) -> int:
        """Return the number of centre-line nodes."""
        return len(self.centre_line)

    def __iter__(self) -> Iterator[np.ndarray]:
        """Iterate over the centre-line nodes."""
        return iter(self.centre_line)

    def __repr__(self) -> str:
        """Return the track name and its size."""
        return f"<Track {self.name!r} nodes={len(self)} width={self.width:.0f}>"
