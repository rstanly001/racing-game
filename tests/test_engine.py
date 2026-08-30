"""Tests for the physics engine.

The engine never renders anything, so a step here is exactly the step an
interactive frame takes.
"""

import numpy as np
import pytest

from racing import PhysicsEngine, PlayerCar, Track, VehicleSpec
from racing.config import PHYSICS_DT


@pytest.fixture
def engine(track: Track) -> PhysicsEngine:
    return PhysicsEngine(track)


@pytest.fixture
def car(spec: VehicleSpec, track: Track) -> PlayerCar:
    return PlayerCar(spec, track, position=(100.0, 100.0), heading=0.0)


def drive(engine: PhysicsEngine, car: PlayerCar, seconds: float, **controls) -> None:
    """Hold a set of controls for a while."""
    for _ in range(int(seconds / PHYSICS_DT)):
        car.throttle = controls.get("throttle", 0.0)
        car.brake = controls.get("brake", 0.0)
        car.steering = controls.get("steering", 0.0)
        engine.step([car])


def test_throttle_accelerates_along_the_heading(engine, car) -> None:
    drive(engine, car, 1.0, throttle=1.0)
    assert car.speed > 0
    assert car.position[1] < 100.0  # heading zero is north, and y grows down


def test_a_coasting_car_slows_down(engine, car) -> None:
    drive(engine, car, 1.0, throttle=1.0)
    rolling = car.speed
    drive(engine, car, 1.0)
    assert car.speed < rolling


def test_speed_is_capped_at_the_specification(engine, car) -> None:
    drive(engine, car, 30.0, throttle=1.0)
    assert car.speed <= car.spec.max_speed + 1e-9


def test_braking_stops_the_car_without_reversing_it(engine, car) -> None:
    drive(engine, car, 2.0, throttle=1.0)
    forward = car.forward.copy()
    drive(engine, car, 5.0, brake=1.0)
    assert car.speed == pytest.approx(0.0)
    assert float(np.dot(car.velocity, forward)) >= 0.0


def test_a_standing_car_cannot_steer(engine, car) -> None:
    drive(engine, car, 1.0, steering=1.0)
    assert car.heading == pytest.approx(0.0)


def test_steering_turns_a_moving_car(engine, car) -> None:
    drive(engine, car, 1.0, throttle=1.0)
    drive(engine, car, 0.5, throttle=1.0, steering=1.0)
    assert car.heading > 0.0


def test_turning_bleeds_off_speed(engine, car) -> None:
    drive(engine, car, 2.0, throttle=1.0)
    straight_line = car.speed
    drive(engine, car, 1.0, throttle=1.0, steering=1.0)
    assert car.speed < straight_line


def test_no_turn_rate_at_a_standstill(engine, car) -> None:
    assert engine.turn_scale(car) == pytest.approx(0.0)


def test_turn_rate_falls_away_at_high_speed(engine, car) -> None:
    car.velocity = car.forward * 150.0
    moderate = engine.turn_scale(car)
    car.velocity = car.forward * car.spec.max_speed
    assert 0.0 < engine.turn_scale(car) < moderate


def test_the_same_inputs_give_the_same_race(spec, track) -> None:
    def run() -> tuple[float, float]:
        car = PlayerCar(spec, track, position=(100.0, 100.0))
        engine = PhysicsEngine(track)
        drive(engine, car, 2.0, throttle=1.0, steering=0.6)
        return tuple(car.position)

    assert run() == run()
