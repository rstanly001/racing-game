"""A 2D racing game with a physics engine, computer opponents, and telemetry.

The package can be played interactively, or stepped with no window at all.
Its building blocks are exported here so they can be imported directly::

    from racing import ComputerCar, GameConfig, Race, VehicleSpec
    from racing.track import build_oval

    track = build_oval()
    cars = [
        ComputerCar(VehicleSpec(name="Red"), track, aggression=0.9),
        ComputerCar(VehicleSpec(name="Blue"), track, aggression=0.7),
    ]

    result = Race(track, cars, GameConfig(laps=3)).run()
    print(result.winner.name, result.winner.best_lap)
"""

from racing.config import GameConfig, VehicleSpec
from racing.entities.computer import ComputerCar
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
    "AssetLoadError",
    "ComputerCar",
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
