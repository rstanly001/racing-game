"""The human-controlled car."""

from __future__ import annotations

from typing import Any

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

        Parameters
        ----------
        dt
            Timestep in seconds.
        **context
            Must contain ``keys``, a container supporting ``in`` that holds
            the names of currently pressed keys, e.g. ``{"up", "left"}``.
        """
        # TODO: implement; smooth the steering with dt so it ramps in
        raise NotImplementedError
