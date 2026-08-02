"""The physics engine: fixed-timestep stepping and collision resolution."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from racing.config import PHYSICS_DT

if TYPE_CHECKING:
    from racing.entities.vehicle import Vehicle
    from racing.track.track import Track

logger = logging.getLogger(__name__)


class PhysicsEngine:
    """Advances every vehicle by one fixed timestep and resolves contacts.

    The engine is deliberately independent of pygame, so it can be stepped in
    a headless simulation exactly as it is during interactive play.

    Parameters
    ----------
    track
        The track, used for boundary checks.
    dt
        Fixed timestep in seconds.
    """

    def __init__(self, track: Track, dt: float = PHYSICS_DT) -> None:
        self.track = track
        self.dt = dt

    def step(self, vehicles: list[Vehicle]) -> None:
        """Advance the whole simulation by one timestep.

        For each vehicle: read its control inputs, apply engine and brake
        forces, apply drag and grip, integrate, then resolve collisions with
        the track boundary and with other vehicles.

        Parameters
        ----------
        vehicles
            Every vehicle in the race.
        """
        # TODO: implement
        raise NotImplementedError

    def apply_controls(self, vehicle: Vehicle) -> None:
        """Convert a vehicle's throttle, brake, and steering into forces."""
        # TODO: implement
        raise NotImplementedError

    def apply_drag(self, vehicle: Vehicle) -> None:
        """Apply air resistance opposing the direction of travel."""
        # TODO: implement
        raise NotImplementedError

    def resolve_track_collision(self, vehicle: Vehicle) -> bool:
        """Push a vehicle back inside the track if it has left it.

        Returns
        -------
        bool
            ``True`` if a collision occurred, so the caller can trigger a
            sound effect and log the event in telemetry.
        """
        # TODO: implement
        raise NotImplementedError

    def resolve_vehicle_collision(self, a: Vehicle, b: Vehicle) -> bool:
        """Resolve a contact between two vehicles with an elastic impulse.

        Returns
        -------
        bool
            ``True`` if the vehicles were overlapping and were separated.
        """
        # TODO: implement using the mass-weighted impulse along the normal
        raise NotImplementedError

    @staticmethod
    def clamp(value: float, low: float, high: float) -> float:
        """Return ``value`` restricted to the range ``[low, high]``."""
        return float(np.clip(value, low, high))
