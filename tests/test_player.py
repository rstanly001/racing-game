"""Tests for keyboard control of the player car.

The player car never imports pygame, so its controls can be driven from a
plain set of key names.
"""

import pytest

from racing import PlayerCar, Track, VehicleSpec


@pytest.fixture
def car(spec: VehicleSpec, track: Track) -> PlayerCar:
    return PlayerCar(spec, track, position=(0.0, 0.0))


def test_no_keys_means_no_input(car: PlayerCar) -> None:
    car.update_controls(0.1, keys=set())
    assert (car.throttle, car.brake, car.steering) == (0.0, 0.0, 0.0)


def test_missing_key_set_is_treated_as_no_input(car: PlayerCar) -> None:
    car.update_controls(0.1)
    assert car.throttle == 0.0


def test_up_applies_throttle(car: PlayerCar) -> None:
    car.update_controls(0.1, keys={"up"})
    assert car.throttle == 1.0
    assert car.brake == 0.0


def test_down_applies_the_brake(car: PlayerCar) -> None:
    car.update_controls(0.1, keys={"down"})
    assert car.brake == 1.0


def test_steering_ramps_in_rather_than_snapping(car: PlayerCar) -> None:
    car.update_controls(1 / 60, keys={"right"})
    assert 0.0 < car.steering < 1.0


def test_steering_reaches_full_lock_when_held(car: PlayerCar) -> None:
    for _ in range(60):
        car.update_controls(1 / 60, keys={"left"})
    assert car.steering == pytest.approx(-1.0)


def test_steering_returns_to_centre_when_released(car: PlayerCar) -> None:
    for _ in range(60):
        car.update_controls(1 / 60, keys={"right"})
    for _ in range(60):
        car.update_controls(1 / 60, keys=set())
    assert car.steering == pytest.approx(0.0)


def test_opposite_keys_cancel_out(car: PlayerCar) -> None:
    car.update_controls(1 / 60, keys={"left", "right"})
    assert car.steering == pytest.approx(0.0)
