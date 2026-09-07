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

# What happens at the edge of the track: how much of the speed driven into
# the barrier comes back as a bounce, and the fraction of speed left after a
# second of scraping along it.
WALL_BOUNCE = 0.25
WALL_SCRUB = 0.6

# How the computer driver reads the road ahead. It looks one distance ahead
# to decide where to point, and a longer one to decide how hard the corner
# is; a bend of CORNER_FULL_ANGLE degrees over that distance counts as the
# tightest corner there is.
CORNER_LOOKAHEAD = 260.0
CORNER_FULL_ANGLE = 75.0

# Fraction of top speed given up in the tightest corner, and the steering
# error in degrees that calls for full lock. Both were found by sweeping them
# against lap time and wall contacts: braking harder than this loses more
# time than the corner ever costs.
CORNER_SLOWDOWN = 0.30
FULL_LOCK_ERROR = 16.0

# How far ahead a computer driver notices a rival, and how far to one side it
# aims to get past. Every driver follows the same racing line, so without a
# nudge two of them converge on it and travel locked together.
OVERTAKE_RANGE = 100.0
OVERTAKE_OFFSET = 34.0

# How nearly straight ahead a rival has to be before it counts as being in
# the way, as the cosine of the angle off the nose. Without it a driver
# swerves around cars beside it that it was never going to hit.
OVERTAKE_CONE = 0.4

# Once a computer driver lifts off, it waits until it has fallen this far
# below its target before picking the throttle back up. Without the gap it
# sits exactly on the limit, flicking the throttle on and off every frame.
THROTTLE_HYSTERESIS = 0.97

# How far over its target a driver has to be before it brakes rather than
# simply lifting off.
BRAKE_MARGIN = 1.05

# Share of its cornering limit the most timid driver settles for. This is
# what makes aggression worth setting: at 1.0 every driver would be equally
# quick and the field would never spread out.
TIMID_MARGIN = 0.6

# How much of the room between the centre line and the edge a racing line is
# allowed to use when cutting the inside of a corner, and how many nodes the
# result is averaged over to smooth it out.
RACING_LINE_CUT = 0.6
RACING_LINE_SMOOTHING = 7

# Speed driven into a barrier, in pixels per second, below which the contact
# counts as a graze: still corrected, but not reported as a collision. The
# nearest point on a polyline is never exactly perpendicular, so a car running
# along a wall always has a trace of speed pointed at it.
IMPACT_SPEED = 20.0

# How close the centres of two cars may get, treating each body as a circle.
# Halfway between the car's length and its width: a pair of discs the size of
# the car itself could never run side by side.
CONTACT_DISTANCE = (CAR_LENGTH + CAR_WIDTH) / 2

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
    record_telemetry
        Whether to record per-frame telemetry.
    """

    laps: int = 3
    record_telemetry: bool = True
