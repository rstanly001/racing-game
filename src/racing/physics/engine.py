"""The physics engine: fixed-timestep stepping and collision resolution."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from racing.config import (
    HIGH_SPEED_STABILITY,
    PHYSICS_DT,
    STEERING_FULL_SPEED,
)
from racing.physics.body import unit

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
            Every vehicle in the race. Their controls must already be set.
        """
        for vehicle in vehicles:
            self.apply_controls(vehicle)
            self.apply_drag(vehicle)
            vehicle.apply_grip(vehicle.spec.grip, self.dt)
            vehicle.integrate(self.dt)

        # TODO: resolve track and vehicle collisions once they exist

    def apply_controls(self, vehicle: Vehicle) -> None:
        """Convert a vehicle's throttle, brake, and steering into motion.

        Steering rotates the car, and grip is what turns that rotation into
        a change of direction: the body keeps travelling the old way until
        :meth:`~racing.physics.body.PhysicsBody.apply_grip` damps the
        sideways velocity that the rotation just created.
        """
        spec = vehicle.spec

        vehicle.heading += (
            vehicle.steering * spec.turn_rate * self.turn_scale(vehicle) * self.dt
        )

        if vehicle.throttle:
            vehicle.apply_force(
                vehicle.forward * spec.acceleration * vehicle.throttle, self.dt
            )

        if vehicle.brake and vehicle.speed:
            # Braking may slow a car to a stop but never drag it backwards.
            slowing = min(spec.brake_force * vehicle.brake * self.dt, vehicle.speed)
            vehicle.velocity -= unit(vehicle.velocity) * slowing

    def turn_scale(self, vehicle: Vehicle) -> float:
        """Return what fraction of the full turn rate is available right now.

        Steering scales with speed in both directions. A stationary car
        cannot turn at all, because its wheels have nothing to push against;
        a car near its top speed gives up some of its turn rate, which is
        what stops fast corners from being free.

        Returns
        -------
        float
            A factor between 0 and 1, applied to ``spec.turn_rate``.
        """
        speed = vehicle.speed
        ramp = min(speed / STEERING_FULL_SPEED, 1.0)
        taper = 1.0 - HIGH_SPEED_STABILITY * min(speed / vehicle.spec.max_speed, 1.0)
        return ramp * taper

    def apply_drag(self, vehicle: Vehicle) -> None:
        """Apply air resistance and hold the car at or below its top speed."""
        spec = vehicle.spec
        vehicle.velocity *= max(0.0, 1.0 - spec.drag * self.dt)

        if vehicle.speed > spec.max_speed:
            vehicle.velocity = unit(vehicle.velocity) * spec.max_speed

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
