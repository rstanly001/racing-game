"""The human-controlled car."""

from __future__ import annotations

from typing import Any

from racing.config import STEERING_RAMP, STEERING_RETURN
from racing.entities.vehicle import Vehicle


class PlayerCar(Vehicle):
    """A car driven from the keyboard.

    Controls are the arrow keys: up for throttle, down for brake, left and
    right to steer.

    Notes
    -----
    This class never imports pygame. The set of currently pressed keys is
    passed in by the caller, which keeps the class testable and lets a
    recorded input sequence be replayed headlessly.
    """

    @property
    def is_human(self) -> bool:
        """Return ``True``: this car is driven by a person."""
        return True

    def update_controls(self, dt: float, **context: Any) -> None:
        """Read the pressed keys from ``context`` and set the controls.

        Throttle and brake are on or off, but steering is smoothed: holding
        a key ramps the input toward full lock, and releasing it lets the
        wheel fall back to centre. Applying full lock on the first frame
        makes the car feel like it is snapping rather than turning.

        Parameters
        ----------
        dt
            Timestep in seconds.
        **context
            Must contain ``keys``, a container supporting ``in`` that holds
            the names of currently pressed keys, e.g. ``{"up", "left"}``.
        """
        keys = context.get("keys") or ()

        self.throttle = 1.0 if "up" in keys else 0.0
        self.brake = 1.0 if "down" in keys else 0.0

        target = float("right" in keys) - float("left" in keys)
        rate = STEERING_RAMP if target else STEERING_RETURN
        self.steering = _approach(self.steering, target, rate * dt)


def _approach(value: float, target: float, step: float) -> float:
    """Move ``value`` toward ``target`` by at most ``step``."""
    if abs(target - value) <= step:
        return target
    return value + step if target > value else value - step
