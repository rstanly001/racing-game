"""Tests for the computer-controlled driver.

The driver is stepped through real races here rather than checked frame by
frame: the thing worth asserting is that it gets round, cleanly, and that
its two tuning knobs do what they claim.
"""

import numpy as np
import pytest

from racing import ComputerCar, GameConfig, Race, Track, VehicleSpec
from racing.track import build_oval


@pytest.fixture
def oval() -> Track:
    return build_oval()


@pytest.fixture
def driver(spec: VehicleSpec, oval: Track) -> ComputerCar:
    return ComputerCar(spec, oval, position=tuple(oval.start_position))


def race_alone(oval: Track, laps: int = 2, **settings) -> ComputerCar:
    """Send one driver round on its own and hand it back."""
    car = ComputerCar(VehicleSpec(name="Solo"), oval, **settings)
    Race(oval, [car], GameConfig(laps=laps)).run(max_seconds=120.0)
    return car


def test_a_computer_driver_is_not_human(driver: ComputerCar) -> None:
    assert driver.is_human is False


def test_it_aims_at_a_point_on_the_racing_line(
    driver: ComputerCar, oval: Track
) -> None:
    assert any(np.allclose(driver.target_point(), point) for point in oval.racing_line)


def test_it_aims_roughly_a_lookahead_ahead(driver: ComputerCar, oval: Track) -> None:
    gap = driver.distance_to(driver.target_point())
    assert 0.5 * driver.lookahead < gap < 1.5 * driver.lookahead


def test_it_aims_forward_rather_than_behind(driver: ComputerCar, oval: Track) -> None:
    driver.heading = oval.start_heading
    assert float(np.dot(driver.target_point() - driver.position, driver.forward)) > 0


def test_corner_severity_stays_in_range(driver: ComputerCar, oval: Track) -> None:
    for node in oval.centre_line[::10]:
        driver.position = np.array(node, dtype=float)
        assert 0.0 <= driver.corner_severity() <= 1.0


def test_the_tight_end_reads_as_a_harder_corner(
    driver: ComputerCar, oval: Track
) -> None:
    # An ellipse bends hardest at the ends of its long axis and least at the
    # ends of its short one.
    driver.position = np.array(oval.centre_line[0], dtype=float)
    tight = driver.corner_severity()
    driver.position = np.array(oval.centre_line[len(oval) // 4], dtype=float)
    assert tight > driver.corner_severity()


def test_it_wants_to_go_slower_in_a_corner(driver: ComputerCar, oval: Track) -> None:
    driver.position = np.array(oval.centre_line[len(oval) // 4], dtype=float)
    on_the_straight = driver.target_speed()
    driver.position = np.array(oval.centre_line[0], dtype=float)
    assert driver.target_speed() < on_the_straight


def test_a_bolder_driver_wants_more_speed(spec: VehicleSpec, oval: Track) -> None:
    bold = ComputerCar(spec, oval, aggression=1.0)
    timid = ComputerCar(spec, oval, aggression=0.5)
    assert bold.target_speed() > timid.target_speed()


def test_it_gets_round_the_oval(oval: Track) -> None:
    car = race_alone(oval)
    assert car.lap == 2
    assert car.best_lap is not None


def test_it_gets_round_without_hitting_anything(oval: Track) -> None:
    assert race_alone(oval).collisions == 0


def test_it_stays_on_the_track_the_whole_way(oval: Track) -> None:
    car = ComputerCar(VehicleSpec(name="Solo"), oval)
    race = Race(oval, [car], GameConfig(laps=1))

    while not race.is_complete() and race.time < 60.0:
        race.step()
        assert oval.contains(car.position)


def test_a_bolder_driver_laps_quicker(oval: Track) -> None:
    bold = race_alone(oval, aggression=1.0)
    timid = race_alone(oval, aggression=0.6)
    assert bold.best_lap < timid.best_lap


def test_the_same_field_gives_the_same_race(oval: Track) -> None:
    def run() -> list[tuple[str, int, float]]:
        cars = [
            ComputerCar(VehicleSpec(name="A"), oval, aggression=0.9),
            ComputerCar(VehicleSpec(name="B"), oval, aggression=0.7),
        ]
        result = Race(oval, cars, GameConfig(laps=2)).run(max_seconds=120.0)
        return [(car.name, car.lap, car.best_lap) for car in result.finish_order]

    assert run() == run()


def test_two_drivers_race_without_touching(oval: Track) -> None:
    # They follow the same racing line, so without the avoidance nudge they
    # converge on it and travel locked together, bumping the whole way.
    cars = [
        ComputerCar(VehicleSpec(name="Timid"), oval, aggression=0.6),
        ComputerCar(VehicleSpec(name="Bold"), oval, aggression=1.0),
    ]
    Race(oval, cars, GameConfig(laps=2)).run(max_seconds=120.0)
    assert [car.collisions for car in cars] == [0, 0]


def test_a_full_field_all_finishes(oval: Track) -> None:
    cars = [
        ComputerCar(VehicleSpec(name=f"Car {n}"), oval, aggression=0.6 + 0.1 * n)
        for n in range(4)
    ]
    result = Race(oval, cars, GameConfig(laps=2)).run(max_seconds=180.0)
    assert len(result.finish_order) == 4
    assert all(car.lap == 2 for car in cars)
