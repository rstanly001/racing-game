"""Configuration objects and tuning constants.

Keeping every magic number here means the physics can be tuned without
touching the simulation code, and the same values are used by the
interactive game and the headless simulator.
"""

from __future__ import annotations

from dataclasses import dataclass

# Fixed simulation timestep, in seconds. The physics integrates at this rate
# regardless of the render frame rate, so a headless run and an interactive
# run produce identical results.
PHYSICS_DT = 1.0 / 60.0

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 60


@dataclass(frozen=True)
class VehicleSpec:
    """Performance characteristics of one car.

    Parameters
    ----------
    name
        Display name, e.g. ``"Red"``.
    max_speed
        Top speed in pixels per second.
    acceleration
        Forward acceleration in pixels per second squared.
    brake_force
        Deceleration under braking, in pixels per second squared. Should be
        noticeably larger than ``acceleration`` to feel right.
    turn_rate
        Maximum steering rate in degrees per second at full lock.
    grip
        Lateral friction coefficient between 0 and 1. Lower values slide.
    drag
        Air resistance coefficient applied against velocity.
    colour
        RGB triple used when rendering.

    Raises
    ------
    ConfigurationError
        If any value is outside its sensible range.
    """

    name: str
    max_speed: float = 420.0
    acceleration: float = 260.0
    brake_force: float = 480.0
    turn_rate: float = 180.0
    grip: float = 0.92
    drag: float = 0.4
    colour: tuple[int, int, int] = (220, 60, 60)

    def __post_init__(self) -> None:
        """Validate the specification."""
        # TODO: raise ConfigurationError for non-positive speeds or a grip
        #       value outside [0, 1]
        raise NotImplementedError


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
