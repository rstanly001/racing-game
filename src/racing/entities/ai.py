"""The computer-controlled car."""

from __future__ import annotations

from typing import Any

import numpy as np

from racing.entities.vehicle import Vehicle


class AICar(Vehicle):
    """A car that follows the track's racing line.

    The controller steers toward a point on the racing line a short distance
    ahead, and brakes when the corner ahead is tighter than its current
    speed allows. ``lookahead`` and ``aggression`` together determine how
    quick and how clean the AI is, which makes difficulty easy to tune.

    Parameters
    ----------
    lookahead
        Distance in pixels to the target point on the racing line. Larger
        values cut corners and give smoother, faster lines.
    aggression
        Between 0 and 1. Scales cornering speed, so a higher value means a
        faster but less stable driver.
    """

    def __init__(
        self,
        *args: Any,
        lookahead: float = 140.0,
        aggression: float = 0.85,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.lookahead = lookahead
        self.aggression = aggression

    @property
    def is_human(self) -> bool:
        """Return ``False``: this car is driven by the computer."""
        return False

    def target_point(self) -> np.ndarray:
        """Return the point on the racing line to steer toward."""
        # TODO: find the nearest racing-line node, then walk forward along
        #       the line until self.lookahead pixels have been covered
        raise NotImplementedError

    def corner_severity(self) -> float:
        """Return how tight the upcoming corner is, from 0 to 1."""
        # TODO: compare heading to the direction of the line further ahead
        raise NotImplementedError

    def update_controls(self, dt: float, **context: Any) -> None:
        """Steer toward the target point and brake for the corner ahead."""
        # TODO: implement
        raise NotImplementedError
