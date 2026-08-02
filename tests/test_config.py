"""Tests for configuration validation."""

import pytest

from racing import ConfigurationError, VehicleSpec


def test_defaults_are_valid() -> None:
    assert VehicleSpec(name="Red").grip == pytest.approx(0.92)


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
