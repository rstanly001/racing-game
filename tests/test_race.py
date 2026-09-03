"""Tests for the race loop, all headless.

Cars are moved to each checkpoint by hand rather than driven there, so lap
counting can be tested without depending on how well anyone drives.
"""

import numpy as np
import pytest

from racing import GameConfig, PlayerCar, Race, Track, VehicleSpec


@pytest.fixture
def race(spec: VehicleSpec, track: Track, config: GameConfig) -> Race:
    return Race(track, [PlayerCar(spec, track)], config)


def visit(race: Race, index: int, steps: int = 1) -> None:
    """Park the leading car on a checkpoint and let the race step on."""
    car = race.cars[0]
    for _ in range(steps):
        car.position = np.array(race.track.checkpoints[index], dtype=float)
        race.step()


def complete_lap(race: Race) -> None:
    """Take the leading car round every checkpoint in order."""
    for index in list(range(1, race.track.n_checkpoints)) + [0]:
        visit(race, index)


def test_a_race_is_not_complete_at_the_start(race: Race) -> None:
    assert not race.is_complete()


def test_cars_start_behind_the_line_facing_along_the_track(race: Race) -> None:
    car = race.cars[0]
    assert car.speed == pytest.approx(0.0)
    assert car.heading == pytest.approx(race.track.start_heading)
    assert 0.0 < race.track.lap_distance(car.position) <= race.track.lap_length


def test_the_grid_keeps_cars_apart(spec: VehicleSpec, track: Track) -> None:
    cars = [PlayerCar(spec, track) for _ in range(4)]
    race = Race(track, cars, GameConfig(laps=1))
    places = [car.position for car in race.cars]
    gaps = [
        np.linalg.norm(one - other)
        for index, one in enumerate(places)
        for other in places[index + 1 :]
    ]
    assert min(gaps) > 0.0


def test_time_advances_by_one_timestep(race: Race) -> None:
    race.step()
    assert race.time == pytest.approx(race.dt)


def test_a_full_circuit_counts_as_a_lap(race: Race) -> None:
    race.step()  # the grid sits inside the start line's capture radius
    complete_lap(race)
    assert race.cars[0].lap == 1


def test_a_lap_takes_a_measurable_time(race: Race) -> None:
    race.step()
    complete_lap(race)
    assert race.cars[0].lap_times[0] > 0.0


def test_skipping_checkpoints_does_not_count(race: Race) -> None:
    race.step()
    visit(race, race.track.n_checkpoints // 2)
    visit(race, 0)
    assert race.cars[0].lap == 0


def test_the_race_ends_after_the_configured_laps(race: Race) -> None:
    race.step()
    for _ in range(race.config.laps):
        complete_lap(race)
    assert race.is_complete()
    assert race.standings[0] is race.cars[0]


def test_standings_put_the_furthest_car_first(spec: VehicleSpec, track: Track) -> None:
    behind, ahead = PlayerCar(spec, track), PlayerCar(spec, track)
    race = Race(track, [behind, ahead], GameConfig(laps=3))
    ahead.register_checkpoint(0, 0.0)
    ahead.register_checkpoint(1, 1.0)
    assert race.standings == [ahead, behind]


def test_standings_split_a_tie_by_who_is_nearer_the_next_checkpoint(
    spec: VehicleSpec, track: Track
) -> None:
    behind, ahead = PlayerCar(spec, track), PlayerCar(spec, track)
    race = Race(track, [behind, ahead], GameConfig(laps=3))
    ahead.position = np.array(track.checkpoints[0], dtype=float)
    assert race.standings == [ahead, behind]


def test_a_car_on_the_grid_is_not_ranked_as_nearly_home(
    spec: VehicleSpec, track: Track
) -> None:
    # Its lap distance is almost a full lap, but it has crossed nothing.
    grid, running = PlayerCar(spec, track), PlayerCar(spec, track)
    race = Race(track, [grid, running], GameConfig(laps=3))
    running.register_checkpoint(0, 0.0)
    assert race.standings == [running, grid]


def test_reset_returns_the_car_to_the_grid(race: Race) -> None:
    car = race.cars[0]
    grid = car.position.copy()

    race.step()
    complete_lap(race)
    race.reset()

    assert car.lap == 0
    assert car.lap_times == []
    assert car.checkpoint_index == 0
    assert race.time == pytest.approx(0.0)
    assert car.position == pytest.approx(grid)
