"""Tests for the physics body."""

import numpy as np
import pytest

from racing import PhysicsBody


def test_starts_at_rest(body: PhysicsBody) -> None:
    assert body.speed == pytest.approx(0.0)


def test_forward_is_a_unit_vector(body: PhysicsBody) -> None:
    assert np.linalg.norm(body.forward) == pytest.approx(1.0)


def test_right_is_perpendicular_to_forward(body: PhysicsBody) -> None:
    assert float(np.dot(body.forward, body.right)) == pytest.approx(0.0, abs=1e-9)


def test_heading_zero_points_north(body: PhysicsBody) -> None:
    body.heading = 0.0
    assert body.forward[1] < 0  # screen coordinates: y grows downward


def test_heading_wraps_into_one_turn(body: PhysicsBody) -> None:
    body.heading = 450.0
    assert body.heading == pytest.approx(90.0)


def test_negative_heading_wraps_forward(body: PhysicsBody) -> None:
    body.heading = -90.0
    assert body.heading == pytest.approx(270.0)


def test_force_accelerates_by_force_over_mass(body: PhysicsBody) -> None:
    body.mass = 2.0
    body.apply_force(np.array([10.0, 0.0]), 1.0)
    assert body.velocity[0] == pytest.approx(5.0)


def test_integration_moves_along_velocity(body: PhysicsBody) -> None:
    body.velocity = np.array([10.0, 0.0])
    start_x = body.position[0]
    body.integrate(1.0)
    assert body.position[0] == pytest.approx(start_x + 10.0)


def test_full_grip_preserves_forward_speed(body: PhysicsBody) -> None:
    body.velocity = body.forward * 100.0
    body.apply_grip(1.0)
    assert body.speed == pytest.approx(100.0)


def test_grip_removes_lateral_velocity(body: PhysicsBody) -> None:
    body.velocity = body.right * 100.0
    body.apply_grip(0.0)
    assert body.speed == pytest.approx(0.0)
