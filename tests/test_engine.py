"""Tests for the physics engine.

The engine never renders anything, so a step here is exactly the step an
interactive frame takes.
"""

import numpy as np
import pytest

from racing import PhysicsEngine, PlayerCar, Track, VehicleSpec
from racing.config import CONTACT_DISTANCE, PHYSICS_DT


@pytest.fixture
def engine(open_track: Track) -> PhysicsEngine:
    return PhysicsEngine(open_track)


@pytest.fixture
def car(spec: VehicleSpec, open_track: Track) -> PlayerCar:
    return PlayerCar(spec, open_track, position=(100.0, 100.0), heading=0.0)


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


def test_the_same_inputs_give_the_same_race(spec, open_track) -> None:
    def run() -> tuple[float, float]:
        car = PlayerCar(spec, open_track, position=(100.0, 100.0))
        engine = PhysicsEngine(open_track)
        drive(engine, car, 2.0, throttle=1.0, steering=0.6)
        return tuple(car.position)

    assert run() == run()


@pytest.fixture
def bounded(track: Track) -> PhysicsEngine:
    """An engine on a track narrow enough for its barriers to matter."""
    return PhysicsEngine(track)


def placed(spec: VehicleSpec, track: Track, at, heading: float = 0.0) -> PlayerCar:
    """Return a car put down at a given spot."""
    return PlayerCar(spec, track, position=tuple(at), heading=heading)


def test_a_car_on_the_racing_line_is_left_alone(bounded, spec, track) -> None:
    car = placed(spec, track, track.centre_line[10])
    assert bounded.resolve_track_collision(car) is False


def test_a_car_off_the_track_is_put_back_on_it(bounded, spec, track) -> None:
    outside = track.centre_line[10] + track.normals()[10] * track.width
    car = placed(spec, track, outside)
    car.velocity = track.normals()[10] * 200.0

    assert bounded.resolve_track_collision(car) is True
    assert track.distance_from_centre(car.position) <= track.width / 2


def test_the_whole_car_is_kept_inside_the_edge(bounded, spec, track) -> None:
    # Put back on the limit, not on the white line, or half the body would
    # still be hanging over the grass.
    outside = track.centre_line[10] + track.normals()[10] * track.width
    car = placed(spec, track, outside)
    car.velocity = track.normals()[10] * 200.0
    bounded.resolve_track_collision(car)
    assert track.distance_from_centre(car.position) < track.width / 2


def test_hitting_the_barrier_costs_speed(bounded, spec, track) -> None:
    outside = track.centre_line[10] + track.normals()[10] * track.width
    car = placed(spec, track, outside)
    car.velocity = track.normals()[10] * 200.0
    before = car.speed

    bounded.resolve_track_collision(car)
    assert car.speed < before
    assert car.collisions == 1


def test_scraping_along_the_barrier_is_not_a_fresh_impact(bounded, spec, track) -> None:
    edge = track.centre_line[10] + track.normals()[10] * track.width
    car = placed(spec, track, edge)
    car.velocity = track.tangents()[10] * 200.0  # travelling along it, not into it

    bounded.resolve_track_collision(car)
    assert car.collisions == 0


def test_two_cars_apart_are_left_alone(bounded, spec, track) -> None:
    one = placed(spec, track, track.centre_line[10])
    other = placed(spec, track, track.centre_line[40])
    assert bounded.resolve_vehicle_collision(one, other) is False


def test_overlapping_cars_are_pushed_apart(bounded, spec, track) -> None:
    one = placed(spec, track, track.centre_line[10])
    other = placed(spec, track, track.centre_line[10] + np.array([4.0, 0.0]))

    assert bounded.resolve_vehicle_collision(one, other) is True
    assert one.distance_to(other.position) == pytest.approx(CONTACT_DISTANCE)


def test_a_car_running_into_another_is_slowed_by_it(bounded, spec, track) -> None:
    behind = placed(spec, track, track.centre_line[10])
    ahead = placed(spec, track, track.centre_line[10] + np.array([20.0, 0.0]))
    behind.velocity = np.array([150.0, 0.0])

    assert bounded.resolve_vehicle_collision(behind, ahead) is True
    assert behind.velocity[0] < 150.0
    assert ahead.velocity[0] > 0.0
    assert behind.collisions == ahead.collisions == 1


def test_cars_moving_apart_are_separated_but_not_shoved(bounded, spec, track) -> None:
    one = placed(spec, track, track.centre_line[10])
    other = placed(spec, track, track.centre_line[10] + np.array([20.0, 0.0]))
    other.velocity = np.array([300.0, 0.0])

    assert bounded.resolve_vehicle_collision(one, other) is True
    assert one.speed == pytest.approx(0.0)
    assert other.velocity[0] == pytest.approx(300.0)
    assert one.collisions == other.collisions == 0
