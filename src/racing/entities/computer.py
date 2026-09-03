"""The computer-controlled car."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from racing.config import (
    CORNER_FULL_ANGLE,
    CORNER_LOOKAHEAD,
    CORNER_SLOWDOWN,
    FULL_LOCK_ERROR,
    OVERTAKE_CONE,
    OVERTAKE_OFFSET,
    OVERTAKE_RANGE,
    TIMID_MARGIN,
)
from racing.entities.vehicle import Vehicle


class ComputerCar(Vehicle):
    """A car that follows the track's racing line.

    The controller steers toward a point on the racing line a short distance
    ahead, and brakes when the corner ahead is tighter than its current
    speed allows. ``lookahead`` and ``aggression`` together determine how
    quick and how clean the driver is, which makes difficulty easy to tune.

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
        lookahead: float = 170.0,
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
        """Return the point on the racing line to steer toward.

        Aiming at the nearest point on the line would make the car saw at
        the wheel, chasing a target it is already on top of. Aiming a fixed
        distance ahead is what makes the line smooth.
        """
        track = self.track
        here = track.node_distances[track.nearest_index(self.position)]
        ahead = (track.node_distances - here) % track.lap_length
        return track.racing_line[int(np.argmin(np.abs(ahead - self.lookahead)))]

    def corner_severity(self) -> float:
        """Return how tight the upcoming corner is, from 0 to 1.

        Measured as how far the track turns between here and a point further
        on, so a long sweeping bend and a hairpin are told apart by how much
        of the turning is packed into the distance.
        """
        track = self.track
        here = track.nearest_index(self.position)
        spacing = track.lap_length / len(track)
        ahead = here + max(int(CORNER_LOOKAHEAD / spacing), 1)

        swing = track.heading_at(ahead) - track.heading_at(here)
        turn = abs((swing + 180.0) % 360.0 - 180.0)
        return min(turn / CORNER_FULL_ANGLE, 1.0)

    def target_speed(self) -> float:
        """Return the speed this driver wants to be doing right now."""
        limit = self.spec.max_speed * (1.0 - CORNER_SLOWDOWN * self.corner_severity())

        # A timid driver leaves more in hand than a bold one.
        return limit * (TIMID_MARGIN + (1.0 - TIMID_MARGIN) * self.aggression)

    def avoid(self, target: np.ndarray, rivals: Sequence[Vehicle]) -> np.ndarray:
        """Shift the aim point sideways to get around a car close ahead.

        Every driver follows the same racing line, so left alone they
        converge on it and travel locked together, bumping all the way
        round. The nudge is dropped if it would aim off the track, and tried
        on the other side instead.

        Parameters
        ----------
        target
            Where the driver would aim with the road to itself.
        rivals
            The other cars in the race.

        Returns
        -------
        numpy.ndarray
            Somewhere to aim that is not straight at the back of a rival.
        """
        for rival in rivals:
            gap = rival.position - self.position
            distance = float(np.linalg.norm(gap))
            if not 0.0 < distance <= OVERTAKE_RANGE:
                continue
            if float(np.dot(gap / distance, self.forward)) < OVERTAKE_CONE:
                continue  # alongside or behind, so not in the way

            # Go round whichever side the rival is not on.
            away = -1.0 if float(np.dot(gap, self.right)) >= 0.0 else 1.0
            for side in (away, -away):
                nudged = target + self.right * side * OVERTAKE_OFFSET
                if self.track.contains(nudged):
                    return nudged

        return target

    def update_controls(self, dt: float, **context: Any) -> None:
        """Steer toward the target point and brake for the corner ahead.

        Parameters
        ----------
        dt
            Timestep in seconds.
        **context
            May contain ``rivals``, the other cars in the race, which the
            driver aims around rather than through.
        """
        target = self.avoid(self.target_point(), context.get("rivals", ()))
        step = target - self.position
        wanted = float(np.degrees(np.arctan2(step[0], -step[1])))
        error = (wanted - self.heading + 180.0) % 360.0 - 180.0
        self.steering = float(np.clip(error / FULL_LOCK_ERROR, -1.0, 1.0))

        limit = self.target_speed()
        self.throttle = 0.0 if self.speed > limit else 1.0
        self.brake = 1.0 if self.speed > limit * 1.05 else 0.0
