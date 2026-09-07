"""Shared fixtures.

Everything here is built in memory, so the suite never opens a window,
opens a file, or needs a display.
"""

import numpy as np
import pytest

from racing import GameConfig, PhysicsBody, Track, VehicleSpec


@pytest.fixture
def spec() -> VehicleSpec:
    return VehicleSpec(name="Test", max_speed=400.0, acceleration=250.0)


@pytest.fixture
def track() -> Track:
    angles = np.linspace(0.0, 2 * np.pi, 120, endpoint=False)
    centre_line = np.column_stack(
        [640.0 + 400.0 * np.cos(angles), 360.0 + 220.0 * np.sin(angles)]
    )
    return Track(name="Test Oval", centre_line=centre_line, width=120.0)


@pytest.fixture
def open_track() -> Track:
    """A track so wide that its barriers never come into play.

    Tests of the driving forces use this, so that a car cannot wander into
    a wall and have its speed changed by something other than the forces
    being measured.
    """
    angles = np.linspace(0.0, 2 * np.pi, 120, endpoint=False)
    centre_line = np.column_stack(
        [640.0 + 400.0 * np.cos(angles), 360.0 + 220.0 * np.sin(angles)]
    )
    return Track(name="Open", centre_line=centre_line, width=4000.0)


@pytest.fixture
def body() -> PhysicsBody:
    return PhysicsBody(position=(100.0, 100.0), heading=0.0)


@pytest.fixture
def config() -> GameConfig:
    return GameConfig(laps=1)
