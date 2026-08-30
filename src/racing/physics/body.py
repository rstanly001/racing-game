"""Rigid-body state and integration.

Positions, velocities, and headings are stored as numpy arrays, so vector
operations such as rotation, projection, and distance are expressed directly
rather than as component-wise arithmetic.
"""

from __future__ import annotations

import numpy as np


def unit(vector: np.ndarray) -> np.ndarray:
    """Return the unit vector along ``vector``, or zeros if it has no length.

    Parameters
    ----------
    vector
        Any two-element vector.

    Returns
    -------
    numpy.ndarray
        A vector of length one, or ``[0, 0]`` for an input of length zero.
        Normalising a stationary car's velocity is common enough that
        returning zeros beats guarding every call site.
    """
    length = float(np.linalg.norm(vector))
    return np.asarray(vector, dtype=float) / length if length else np.zeros(2)


class PhysicsBody:
    """A body with a position, a velocity, and a heading.

    Parameters
    ----------
    position
        Starting position as ``[x, y]``, in pixels.
    heading
        Starting heading in degrees, measured clockwise from north.
    mass
        Mass in arbitrary units, used for collision response.

    Attributes
    ----------
    position, velocity : numpy.ndarray
        Two-element float arrays.
    heading : float
        Current heading in degrees, always normalised to ``[0, 360)``.
    """

    def __init__(
        self,
        position: tuple[float, float] | np.ndarray,
        heading: float = 0.0,
        mass: float = 1.0,
    ) -> None:
        self.position = np.asarray(position, dtype=float)
        self.velocity = np.zeros(2, dtype=float)
        self.heading = heading
        self.mass = float(mass)

    @property
    def heading(self) -> float:
        """Return the heading in degrees, normalised to ``[0, 360)``."""
        return self._heading

    @heading.setter
    def heading(self, degrees: float) -> None:
        """Store a heading, wrapping it into ``[0, 360)``."""
        self._heading = float(degrees) % 360.0

    @property
    def speed(self) -> float:
        """Return the magnitude of the velocity vector."""
        return float(np.linalg.norm(self.velocity))

    @property
    def forward(self) -> np.ndarray:
        """Return the unit vector pointing along the current heading.

        Screen coordinates put the origin at the top left with ``y`` growing
        downward, so a heading of zero — due north — is ``[0, -1]``.
        """
        radians = np.radians(self._heading)
        return np.array([np.sin(radians), -np.cos(radians)])

    @property
    def right(self) -> np.ndarray:
        """Return the unit vector perpendicular to :attr:`forward`."""
        radians = np.radians(self._heading)
        return np.array([np.cos(radians), np.sin(radians)])

    def apply_force(self, force: np.ndarray, dt: float) -> None:
        """Accelerate the body by ``force / mass`` over ``dt`` seconds."""
        self.velocity += np.asarray(force, dtype=float) * (dt / self.mass)

    def integrate(self, dt: float) -> None:
        """Advance the position by the current velocity over ``dt`` seconds."""
        self.position += self.velocity * dt

    def apply_grip(self, grip: float) -> None:
        """Damp the lateral component of velocity.

        Splits the velocity into forward and lateral components, keeps the
        forward part intact, and scales the lateral part by ``grip``. A grip
        of 1 means no sliding; lower values let the car drift.

        Parameters
        ----------
        grip
            Lateral friction coefficient between 0 and 1.
        """
        forward, right = self.forward, self.right
        along = float(np.dot(self.velocity, forward))
        across = float(np.dot(self.velocity, right))
        self.velocity = forward * along + right * across * grip

    def distance_to(self, point: np.ndarray) -> float:
        """Return the Euclidean distance from this body to ``point``."""
        return float(np.linalg.norm(self.position - np.asarray(point, dtype=float)))

    def __repr__(self) -> str:
        """Return position, heading, and speed."""
        x, y = self.position
        return (
            f"<PhysicsBody pos=({x:.1f}, {y:.1f}) "
            f"hdg={self.heading:.0f}° v={self.speed:.1f}>"
        )
