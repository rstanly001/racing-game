"""Race orchestration: the main loop, shared by interactive and headless runs."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from racing.config import PHYSICS_DT, GameConfig
from racing.physics.engine import PhysicsEngine
from racing.telemetry.recorder import Telemetry

if TYPE_CHECKING:
    import pandas as pd

    from racing.entities.vehicle import Vehicle
    from racing.track.track import Track

logger = logging.getLogger(__name__)


class RaceResult:
    """The outcome of a completed race.

    Parameters
    ----------
    finish_order
        Cars in the order they finished.
    telemetry
        The full recording.
    duration
        Race length in seconds of simulated time.
    """

    def __init__(
        self,
        finish_order: list[Vehicle],
        telemetry: Telemetry,
        duration: float,
    ) -> None:
        self.finish_order = finish_order
        self.telemetry = telemetry
        self.duration = duration

    @property
    def winner(self) -> Vehicle:
        """Return the car that finished first."""
        return self.finish_order[0]

    def to_frame(self) -> pd.DataFrame:
        """Return the telemetry as a DataFrame."""
        return self.telemetry.to_frame()

    def __repr__(self) -> str:
        """Return the winner and the race duration."""
        return f"<RaceResult winner={self.winner.name!r} duration={self.duration:.1f}s>"


class Race:
    """One race between two or more cars on a track.

    The loop steps the physics at a fixed timestep. Rendering, if any, is
    driven separately, which is what lets the identical simulation run with
    or without a window.

    Parameters
    ----------
    track
        The circuit.
    cars
        The competing vehicles.
    config
        Runtime settings.

    Examples
    --------
    >>> race = Race(track, [red, blue], GameConfig(laps=3, headless=True))
    >>> result = race.run()
    >>> result.winner.name
    """

    def __init__(
        self,
        track: Track,
        cars: list[Vehicle],
        config: GameConfig | None = None,
    ) -> None:
        self.track = track
        self.cars = cars
        self.config = config or GameConfig()
        self.engine = PhysicsEngine(track, dt=PHYSICS_DT)
        self.telemetry = Telemetry()
        self.time = 0.0
        self.finished: list[Vehicle] = []

    def step(self, keys: set[str] | None = None) -> None:
        """Advance the race by one fixed physics timestep.

        Parameters
        ----------
        keys
            Names of keys currently pressed, passed through to any human
            driver. ``None`` in a headless run.
        """
        # TODO: update controls, step physics, check checkpoints and laps,
        #       record telemetry, advance self.time
        raise NotImplementedError

    def is_complete(self) -> bool:
        """Return whether every car has finished the required laps."""
        return len(self.finished) == len(self.cars)

    def run(self, max_seconds: float = 600.0) -> RaceResult:
        """Run the race to completion without rendering.

        This is the headless path used by the ``simulate`` command. It runs
        as fast as the CPU allows, with no window, no audio, and no frame
        limiter.

        Parameters
        ----------
        max_seconds
            Safety limit on simulated time, so a stuck car cannot hang the
            process.

        Returns
        -------
        RaceResult
            The finishing order and the full telemetry recording.
        """
        # TODO: loop self.step() until is_complete() or the time limit
        raise NotImplementedError

    def reset(self) -> None:
        """Return every car to the grid and clear the recording."""
        # TODO: implement
        raise NotImplementedError
