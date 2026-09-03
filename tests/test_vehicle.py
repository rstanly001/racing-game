"""Tests for the vehicle hierarchy."""

import pytest

from racing import AICar, PlayerCar, Vehicle


def test_vehicle_is_abstract(spec, track) -> None:
    with pytest.raises(TypeError):
        Vehicle(spec, track, position=(0.0, 0.0))


def test_player_is_human(spec, track) -> None:
    car = PlayerCar(spec, track, position=(0.0, 0.0))
    assert car.is_human is True


def test_ai_is_not_human(spec, track) -> None:
    car = AICar(spec, track, position=(0.0, 0.0))
    assert car.is_human is False


def test_both_subclass_vehicle(spec, track) -> None:
    assert issubclass(PlayerCar, Vehicle)
    assert issubclass(AICar, Vehicle)


def test_best_lap_is_none_before_any_lap(spec, track) -> None:
    car = AICar(spec, track, position=(0.0, 0.0))
    assert car.best_lap is None


def test_checkpoints_must_be_crossed_in_order(spec, track) -> None:
    car = AICar(spec, track, position=(0.0, 0.0))
    car.register_checkpoint(0, 0.0)
    car.register_checkpoint(5, 1.0)  # skipping ahead must be rejected
    assert car.checkpoint_index == 1


def lap(car: Vehicle, at: float, start: float = 0.0) -> bool:
    """Cross every checkpoint in order, finishing on the line at ``at``."""
    step = (at - start) / car.track.n_checkpoints
    for number in range(1, car.track.n_checkpoints):
        car.register_checkpoint(number, start + number * step)
    return car.register_checkpoint(0, at)


def test_the_first_crossing_starts_the_clock(spec, track) -> None:
    car = AICar(spec, track, position=(0.0, 0.0))
    assert car.register_checkpoint(0, 4.0) is False
    assert car.lap == 0
    assert car.lap_started == 4.0


def test_a_full_circuit_completes_a_lap(spec, track) -> None:
    car = AICar(spec, track, position=(0.0, 0.0))
    car.register_checkpoint(0, 0.0)
    assert lap(car, at=30.0) is True
    assert car.lap == 1
    assert car.lap_times == [30.0]


def test_lap_times_are_measured_between_crossings(spec, track) -> None:
    car = AICar(spec, track, position=(0.0, 0.0))
    car.register_checkpoint(0, 0.0)
    lap(car, at=30.0)
    lap(car, at=55.0, start=30.0)
    assert car.lap_times == [30.0, 25.0]
    assert car.best_lap == 25.0


def test_the_start_line_alone_does_not_count_as_a_lap(spec, track) -> None:
    car = AICar(spec, track, position=(0.0, 0.0))
    car.register_checkpoint(0, 0.0)
    assert car.register_checkpoint(0, 1.0) is False
    assert car.lap == 0


def test_a_skipped_checkpoint_blocks_the_lap(spec, track) -> None:
    car = AICar(spec, track, position=(0.0, 0.0))
    car.register_checkpoint(0, 0.0)
    for number in range(2, track.n_checkpoints):  # checkpoint 1 missed
        car.register_checkpoint(number, float(number))
    assert car.register_checkpoint(0, 30.0) is False
    assert car.lap == 0
