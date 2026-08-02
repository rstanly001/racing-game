"""A 2D racing game with a physics engine, an AI opponent, and telemetry.

The package can be played interactively, or run headless to simulate a race
and analyse the resulting telemetry. Its building blocks are exported here so
they can be imported directly::

    from racing import AICar, PhysicsEngine, Race, Track

    track = Track.load("data/tracks/oval.json")
    race = Race(track, cars=[AICar("Red", track), AICar("Blue", track)])
    result = race.run(laps=3, headless=True)
    result.telemetry.to_csv("output/telemetry.csv")
"""

from racing.config import GameConfig, VehicleSpec
from racing.entities.ai import AICar
from racing.entities.player import PlayerCar
from racing.entities.vehicle import Vehicle
from racing.exceptions import (
    AssetLoadError,
    ConfigurationError,
    RacingError,
    TelemetryError,
    TrackError,
)
from racing.game.race import Race, RaceResult
from racing.physics.body import PhysicsBody
from racing.physics.engine import PhysicsEngine
from racing.telemetry.recorder import Telemetry
from racing.track.track import Track

__version__ = "0.1.0"

__all__ = [
    "AICar",
    "AssetLoadError",
    "ConfigurationError",
    "GameConfig",
    "PhysicsBody",
    "PhysicsEngine",
    "PlayerCar",
    "Race",
    "RaceResult",
    "RacingError",
    "Telemetry",
    "TelemetryError",
    "Track",
    "TrackError",
    "Vehicle",
    "VehicleSpec",
    "__version__",
]
