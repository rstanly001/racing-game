"""Configuration objects and tuning constants.

Keeping every magic number here means the physics can be tuned without
touching the simulation code, and the same values are used by the
interactive game and the headless simulator.
"""

from __future__ import annotations

from dataclasses import dataclass

from racing.exceptions import ConfigurationError

# Fixed simulation timestep, in seconds. The physics integrates at this rate
# regardless of the render frame rate, so a headless run and an interactive
# run produce identical results.
PHYSICS_DT = 1.0 / 60.0

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 60

# Car body size in pixels, used both for drawing and for collision radii.
CAR_LENGTH = 34.0
CAR_WIDTH = 18.0

# How fast a steering input ramps in and falls back to centre, in units of
# full lock per second. Instant steering feels twitchy; these smooth it.
STEERING_RAMP = 4.0
STEERING_RETURN = 6.0

# Speed in pixels per second at which the full turn rate becomes available.
# Below it the car turns proportionally less, so a crawling car cannot spin
# on the spot, and a standing car cannot steer at all.
STEERING_FULL_SPEED = 120.0

# Fraction of the turn rate given up at top speed. Cars that steer as hard
# at 400 as at 150 feel weightless, and make every corner trivial.
HIGH_SPEED_STABILITY = 0.45

# Grid layout, in pixels: how far the front row sits behind the start line,
# and the gap back to each row behind it.
GRID_SETBACK = 34.0
GRID_ROW_SPACING = 48.0

# How near a car must pass to a checkpoint for the crossing to count. Wide
# enough to catch a car running off the racing line, narrow enough that
# neighbouring checkpoints never overlap.
CHECKPOINT_RADIUS = 90.0


@dataclass(frozen=True)
class VehicleSpec:
    """Performance characteristics of one car.

    Parameters
    ----------
    name
        Display name, e.g. ``"Red"``.
    max_speed
        Top speed in pixels per second. Drag alone should hold the car just
        below this, leaving the value itself as a safety net rather than a
        wall the car slams into.
    acceleration
        Forward acceleration in pixels per second squared.
    brake_force
        Deceleration under braking, in pixels per second squared. Should be
        noticeably larger than ``acceleration`` to feel right.
    turn_rate
        Maximum steering rate in degrees per second at full lock.
    grip
        Fraction of sideways velocity shed per second, between 0 and 1.
        ``1`` glues the car to the road, ``0.9`` lets it drift, ``0`` is ice.
    drag
        Air resistance, as the fraction of speed lost per second while
        coasting. Together with ``acceleration`` it sets the top speed:
        a car settles at ``acceleration / drag``.
    colour
        RGB triple used when rendering.

    Raises
    ------
    ConfigurationError
        If any value is outside its sensible range.
    """

    name: str
    max_speed: float = 420.0
    acceleration: float = 250.0
    brake_force: float = 420.0
    turn_rate: float = 180.0
    grip: float = 0.99
    drag: float = 0.6
    colour: tuple[int, int, int] = (220, 60, 60)

    def __post_init__(self) -> None:
        """Validate the specification.

        Raises
        ------
        ConfigurationError
            If a name is empty, a rate is not positive, or ``grip`` or
            ``drag`` falls outside its allowed range.
        """
        if not self.name:
            raise ConfigurationError("a vehicle needs a name")

        positive = {
            "max_speed": self.max_speed,
            "acceleration": self.acceleration,
            "brake_force": self.brake_force,
            "turn_rate": self.turn_rate,
        }
        for field, value in positive.items():
            if value <= 0:
                raise ConfigurationError(
                    f"{self.name}: {field} must be positive, got {value}"
                )

        if not 0.0 <= self.grip <= 1.0:
            raise ConfigurationError(
                f"{self.name}: grip must be between 0 and 1, got {self.grip}"
            )
        if self.drag < 0.0:
            raise ConfigurationError(
                f"{self.name}: drag must not be negative, got {self.drag}"
            )


@dataclass
class GameConfig:
    """Runtime settings for one race.

    Parameters
    ----------
    laps
        Number of laps to complete.
    headless
        If ``True``, run with no window and no audio. Required for grading
        on a machine with no display.
    sound
        Whether to play engine and collision audio. Ignored when headless.
    seed
        Seed for any randomness, so a run is exactly reproducible.
    record_telemetry
        Whether to record per-frame telemetry.
    """

    laps: int = 3
    headless: bool = False
    sound: bool = True
    seed: int | None = 42
    record_telemetry: bool = True
