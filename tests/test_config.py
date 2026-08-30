"""Tests for configuration validation."""

import pytest

from racing import ConfigurationError, VehicleSpec


def test_the_defaults_build() -> None:
    assert 0.0 <= VehicleSpec(name="Red").grip <= 1.0


def test_brakes_are_stronger_than_the_engine() -> None:
    spec = VehicleSpec(name="Red")
    assert spec.brake_force > spec.acceleration


def test_drag_alone_holds_the_car_below_its_top_speed() -> None:
    # Otherwise the car accelerates into the max_speed clamp and stops dead
    # there, instead of easing up to a speed drag settles it at.
    spec = VehicleSpec(name="Red")
    assert spec.acceleration / spec.drag <= spec.max_speed


def test_spec_is_frozen(spec: VehicleSpec) -> None:
    with pytest.raises(AttributeError):
        spec.max_speed = 999.0


def test_empty_name_is_rejected() -> None:
    with pytest.raises(ConfigurationError):
        VehicleSpec(name="")


@pytest.mark.parametrize(
    "field", ["max_speed", "acceleration", "brake_force", "turn_rate"]
)
def test_non_positive_rates_are_rejected(field: str) -> None:
    with pytest.raises(ConfigurationError, match=field):
        VehicleSpec(name="Red", **{field: 0.0})


@pytest.mark.parametrize("grip", [-0.1, 1.5])
def test_grip_outside_zero_to_one_is_rejected(grip: float) -> None:
    with pytest.raises(ConfigurationError, match="grip"):
        VehicleSpec(name="Red", grip=grip)


def test_negative_drag_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="drag"):
        VehicleSpec(name="Red", drag=-1.0)
