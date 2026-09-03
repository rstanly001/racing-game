"""Race orchestration: the main loop, shared by interactive and headless runs."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from racing.config import (
    CHECKPOINT_RADIUS,
    GRID_ROW_SPACING,
    GRID_SETBACK,
    PHYSICS_DT,
    GameConfig,
)
from racing.physics.engine import PhysicsEngine
from racing.telemetry.recorder import Telemetry

if TYPE_CHECKING:
    import pandas as pd

    from racing.entities.vehicle import Vehicle
    from racing.track.track import Track

logger = logging.getLogger(__name__)


def _ordinal(place: int) -> str:
    """Return a finishing place as ``1st``, ``2nd``, and so on."""
    if place % 100 in (11, 12, 13):
        return f"{place}th"
    return f"{place}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(place % 10, 'th') }"


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
        self.reset()

    @property
    def dt(self) -> float:
        """Return the fixed physics timestep, in seconds."""
        return self.engine.dt

    @property
    def standings(self) -> list[Vehicle]:
        """Return the cars in race order, leader first.

        Finishers keep the order they finished in. Everyone still running is
        ranked by how far they have got.
        """
        running = [car for car in self.cars if car not in self.finished]
        running.sort(key=self.progress, reverse=True)
        return self.finished + running

    def progress(self, car: Vehicle) -> tuple[int, int, float]:
        """Return how far ``car`` has got, as a sortable tuple.

        Laps first, then checkpoints crossed, then how close the car is to
        the checkpoint it is heading for. Distance around the lap would be
        the obvious tiebreak, but a car sitting on the grid is just behind
        the start line, which is nearly a full lap by that measure.
        """
        target = self.track.checkpoints[car.checkpoint_index]
        return (car.lap, car.checkpoint_index, -car.distance_to(target))

    def grid_slot(self, index: int) -> tuple[np.ndarray, float]:
        """Return the position and heading of the ``index``-th place on the grid.

        Cars are staggered two abreast behind the start line, as they would
        be on a real grid, so nobody begins the race inside a rival.
        """
        row, column = divmod(index, 2)
        setback = GRID_SETBACK + row * GRID_ROW_SPACING
        offset = (column - 0.5) * self.track.width / 3

        position = (
            self.track.start_position
            - self.track.tangents()[0] * setback
            + self.track.normals()[0] * offset
        )
        return position, self.track.start_heading

    def step(self, keys: set[str] | None = None) -> None:
        """Advance the race by one fixed physics timestep.

        Parameters
        ----------
        keys
            Names of keys currently pressed, passed through to any human
            driver. ``None`` in a headless run.
        """
        for car in self.cars:
            rivals = [other for other in self.cars if other is not car]
            car.update_controls(self.dt, keys=keys, rivals=rivals)

        self.engine.step(self.cars)
        self.time += self.dt

        for car in self.cars:
            self.register_crossings(car)

        # TODO: record a telemetry row per car once Telemetry.record exists

    def register_crossings(self, car: Vehicle) -> None:
        """Offer ``car`` every checkpoint it is currently close to.

        Each candidate is offered to the car rather than assumed: the car
        accepts only the one it is due to cross next, so cutting the infield
        past a later checkpoint gains nothing.
        """
        deltas = self.track.checkpoints - car.position
        distances = np.einsum("ij,ij->i", deltas, deltas)

        for index in np.flatnonzero(distances <= CHECKPOINT_RADIUS**2):
            if car.register_checkpoint(int(index), self.time):
                self.finish(car)

    def finish(self, car: Vehicle) -> None:
        """Retire ``car`` from the race if it has completed every lap."""
        if car.lap < self.config.laps or car in self.finished:
            return

        self.finished.append(car)
        logger.info(
            "%s finished %s of %d in %.1fs",
            car.name,
            _ordinal(len(self.finished)),
            len(self.cars),
            self.time,
        )

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
        while not self.is_complete() and self.time < max_seconds:
            self.step()

        if not self.is_complete():
            logger.warning(
                "stopped after %.0fs with %d car(s) still running",
                max_seconds,
                len(self.cars) - len(self.finished),
            )

        return RaceResult(self.standings, self.telemetry, self.time)

    def reset(self) -> None:
        """Return every car to the grid and clear the recording."""
        for index, car in enumerate(self.cars):
            position, heading = self.grid_slot(index)
            car.position = np.array(position, dtype=float)
            car.velocity = np.zeros(2, dtype=float)
            car.heading = heading
            car.throttle = car.brake = car.steering = 0.0
            car.lap = 0
            car.lap_times.clear()
            car.checkpoint_index = 0
            car.lap_started = None
            car.collisions = 0

        self.telemetry = Telemetry()
        self.time = 0.0
        self.finished.clear()
