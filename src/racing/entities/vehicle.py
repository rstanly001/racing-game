"""The abstract :class:`Vehicle` base class.

A vehicle is a :class:`~racing.physics.body.PhysicsBody` that also decides
what its controls should be. Subclasses differ only in how they make that
decision: :class:`~racing.entities.player.PlayerCar` reads the keyboard,
:class:`~racing.entities.ai.AICar` follows the racing line. The physics
engine depends only on this interface, so new controllers can be added
without changing the simulation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from racing.config import VehicleSpec
from racing.physics.body import PhysicsBody

if TYPE_CHECKING:
    from racing.track.track import Track


class Vehicle(PhysicsBody, ABC):
    """A car in the race.

    Parameters
    ----------
    spec
        Performance characteristics of this car.
    track
        The track it is racing on, or ``None`` to drive on open ground.
    position
        Starting position.
    heading
        Starting heading in degrees.

    Attributes
    ----------
    throttle : float
        Current throttle, from 0 to 1.
    brake : float
        Current brake application, from 0 to 1.
    steering : float
        Current steering input, from -1 (full left) to 1 (full right).
    lap : int
        Laps completed.
    lap_times : list of float
        Elapsed time of each completed lap, in seconds.
    """

    def __init__(
        self,
        spec: VehicleSpec,
        track: Track | None = None,
        position: tuple[float, float] = (0.0, 0.0),
        heading: float = 0.0,
    ) -> None:
        super().__init__(position=position, heading=heading, mass=1.0)
        self.spec = spec
        self.track = track
        self.throttle = 0.0
        self.brake = 0.0
        self.steering = 0.0
        self.lap = 0
        self.lap_times: list[float] = []
        self.checkpoint_index = 0
        self.collisions = 0

    @property
    def name(self) -> str:
        """Return the car's display name."""
        return self.spec.name

    @abstractmethod
    def update_controls(self, dt: float, **context: Any) -> None:
        """Set :attr:`throttle`, :attr:`brake`, and :attr:`steering`.

        Called once per physics step, before forces are applied.

        Parameters
        ----------
        dt
            Timestep in seconds.
        **context
            Extra information a controller may need, such as pressed keys
            for a human player or rival positions for the AI.
        """

    @property
    @abstractmethod
    def is_human(self) -> bool:
        """Return whether this car is controlled by a person."""

    def register_checkpoint(self, index: int, elapsed: float) -> bool:
        """Record passing a checkpoint, completing a lap if it was the last.

        Parameters
        ----------
        index
            Index of the checkpoint that was crossed.
        elapsed
            Race time in seconds at the moment of crossing.

        Returns
        -------
        bool
            ``True`` if this crossing completed a lap.
        """
        # TODO: implement — only accept the next checkpoint in sequence, so
        #       the lap counter cannot be cheated by driving backwards
        raise NotImplementedError

    @property
    def best_lap(self) -> float | None:
        """Return the fastest completed lap time, or ``None`` if no laps."""
        return min(self.lap_times) if self.lap_times else None

    def __repr__(self) -> str:
        """Return the name, lap count, and current speed."""
        return (
            f"<{type(self).__name__} {self.name!r} lap={self.lap} v={self.speed:.0f}>"
        )
