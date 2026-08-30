"""Track geometry, checkpoints, and the racing line."""

from __future__ import annotations

import json  # noqa: F401  (used once load/save are implemented)
import logging
from collections.abc import Iterator
from functools import cached_property
from pathlib import Path

import numpy as np

from racing.exceptions import TrackError

logger = logging.getLogger(__name__)

# A centre line needs at least this many nodes to close into a loop.
MIN_NODES = 3


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

    Raises
    ------
    TrackError
        If the centre line is not a closed loop of at least three ``(x, y)``
        nodes, the width is not positive, or there are more checkpoints than
        nodes to place them on.
    """

    def __init__(
        self,
        name: str,
        centre_line: np.ndarray,
        width: float = 120.0,
        n_checkpoints: int = 12,
    ) -> None:
        centre_line = np.asarray(centre_line, dtype=float)

        if centre_line.ndim != 2 or centre_line.shape[1] != 2:
            raise TrackError(
                f"{name}: the centre line must have shape (n, 2), "
                f"got {centre_line.shape}"
            )
        if len(centre_line) < MIN_NODES:
            raise TrackError(
                f"{name}: a centre line needs at least {MIN_NODES} nodes, "
                f"got {len(centre_line)}"
            )
        if width <= 0:
            raise TrackError(f"{name}: width must be positive, got {width}")
        if not 1 <= n_checkpoints <= len(centre_line):
            raise TrackError(
                f"{name}: n_checkpoints must be between 1 and "
                f"{len(centre_line)}, got {n_checkpoints}"
            )

        self.name = name
        self.centre_line = centre_line
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

    @cached_property
    def checkpoint_indices(self) -> np.ndarray:
        """Return the centre-line indices the checkpoints sit on."""
        spacing = len(self.centre_line) / self.n_checkpoints
        return (np.arange(self.n_checkpoints) * spacing).astype(int)

    @cached_property
    def checkpoints(self) -> np.ndarray:
        """Return checkpoint positions, evenly spaced along the centre line."""
        return self.centre_line[self.checkpoint_indices]

    @property
    def start_position(self) -> np.ndarray:
        """Return the position of the start/finish line."""
        return self.centre_line[0]

    @property
    def start_heading(self) -> float:
        """Return the heading a car should start with, in degrees.

        Taken from the first centre-line segment, so a car placed on the grid
        faces along the track rather than across it.
        """
        return self.heading_at(0)

    def heading_at(self, index: int) -> float:
        """Return the direction of travel at centre-line node ``index``.

        Parameters
        ----------
        index
            Node index, wrapped around the loop.

        Returns
        -------
        float
            Heading in degrees, clockwise from north.
        """
        nodes = self.centre_line
        step = nodes[(index + 1) % len(nodes)] - nodes[index % len(nodes)]
        return float(np.degrees(np.arctan2(step[0], -step[1])) % 360.0)

    def tangents(self) -> np.ndarray:
        """Return the unit direction of travel at every centre-line node.

        Each tangent spans the neighbouring nodes rather than the next one
        alone, which keeps the direction smooth where segments meet.
        """
        nodes = self.centre_line
        spans = np.roll(nodes, -1, axis=0) - np.roll(nodes, 1, axis=0)
        lengths = np.linalg.norm(spans, axis=1, keepdims=True)
        return spans / np.where(lengths == 0.0, 1.0, lengths)

    def normals(self) -> np.ndarray:
        """Return the unit vector pointing left of travel at every node."""
        tangents = self.tangents()
        return np.column_stack([tangents[:, 1], -tangents[:, 0]])

    def boundaries(self) -> tuple[np.ndarray, np.ndarray]:
        """Return the two track edges, offset from the centre line.

        Returns
        -------
        tuple of numpy.ndarray
            The left and right edges, each of shape ``(n, 2)``, obtained by
            stepping half a track width along the normals in both directions.
        """
        offsets = self.normals() * (self.width / 2)
        return self.centre_line + offsets, self.centre_line - offsets

    def racing_line(self) -> np.ndarray:
        """Return the line a driver aims to follow.

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n, 2)``. For now this is the centre line; a
            later version pulls it toward the inside of corners and lets it
            run wide again on exit.
        """
        return self.centre_line.copy()

    def distance_from_centre(self, point: np.ndarray) -> float:
        """Return the shortest distance from ``point`` to the centre line.

        The distance is measured to the nearest point on any segment, not to
        the nearest node, so a wide-spaced centre line does not report a car
        as being off track halfway between two nodes.

        Parameters
        ----------
        point
            A single ``(x, y)`` position.

        Returns
        -------
        float
            Distance in pixels.
        """
        deltas = point - self._closest_points(point)
        return float(np.sqrt(np.einsum("ij,ij->i", deltas, deltas).min()))

    def _closest_points(self, point: np.ndarray) -> np.ndarray:
        """Return the closest point on each centre-line segment to ``point``.

        Every segment is handled in one vectorised pass: project the point
        onto each segment, clamp the projection to the segment's ends, and
        return where it landed.
        """
        point = np.asarray(point, dtype=float)
        starts = self.centre_line
        edges = np.roll(starts, -1, axis=0) - starts

        lengths_sq = np.einsum("ij,ij->i", edges, edges)
        lengths_sq = np.where(lengths_sq == 0.0, 1.0, lengths_sq)
        along = np.einsum("ij,ij->i", point - starts, edges) / lengths_sq

        return starts + edges * np.clip(along, 0.0, 1.0)[:, None]

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
