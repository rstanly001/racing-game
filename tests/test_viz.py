"""Tests for the analysis figures.

Nothing here inspects a picture. What is worth pinning is that a file gets
written, that the backend can never open a window, and that a car keeps the
same colour across every figure.
"""

import matplotlib
import pandas as pd
import pytest

from racing import ComputerCar, GameConfig, Race, TelemetryError, VehicleSpec
from racing.telemetry.recorder import COLUMNS
from racing.track import build_oval
from racing.viz import plot_all, plot_inputs, plot_lap_times, plot_racing_line
from racing.viz.plots import SERIES, _cars, _colour


@pytest.fixture(scope="module")
def telemetry() -> pd.DataFrame:
    """One finished race, shared by every test in this file."""
    track = build_oval()
    cars = [
        ComputerCar(VehicleSpec(name="Blue"), track, aggression=0.9),
        ComputerCar(VehicleSpec(name="Gold"), track, aggression=0.7),
    ]
    return Race(track, cars, GameConfig(laps=2)).run(max_seconds=120.0).to_frame()


def test_the_backend_can_never_open_a_window() -> None:
    assert matplotlib.get_backend().lower() == "agg"


def test_every_figure_is_written(telemetry, tmp_path) -> None:
    paths = plot_all(telemetry, tmp_path)

    assert len(paths) == 4
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)


def test_figures_are_named_for_what_they_show(telemetry, tmp_path) -> None:
    names = {path.name for path in plot_all(telemetry, tmp_path)}
    assert names == {
        "speed_trace.png",
        "racing_line.png",
        "lap_times.png",
        "inputs.png",
    }


def test_a_missing_directory_is_created(telemetry, tmp_path) -> None:
    path = plot_lap_times(telemetry, tmp_path / "deep" / "down" / "laps.png")
    assert path.exists()


def test_each_plot_returns_the_path_it_wrote(telemetry, tmp_path) -> None:
    wanted = tmp_path / "inputs.png"
    assert plot_inputs(telemetry, wanted) == wanted


def test_a_car_keeps_one_colour_everywhere(telemetry) -> None:
    cars = _cars(telemetry)
    assert [_colour(cars, car) for car in cars] == SERIES[: len(cars)]


def test_colours_are_assigned_in_order_not_cycled(telemetry) -> None:
    # Adding a car must not repaint the ones already there.
    cars = _cars(telemetry)
    assert _colour(cars + ["Zebra"], cars[0]) == _colour(cars, cars[0])


def test_an_empty_recording_is_reported(tmp_path) -> None:
    with pytest.raises(TelemetryError, match="no telemetry"):
        plot_racing_line(pd.DataFrame(columns=COLUMNS), tmp_path / "empty.png")


def test_more_cars_than_colours_is_reported(telemetry, tmp_path) -> None:
    crowd = pd.concat(
        [telemetry.assign(car=f"Car {n}") for n in range(len(SERIES) + 1)],
        ignore_index=True,
    )

    with pytest.raises(TelemetryError, match="palette holds"):
        plot_lap_times(crowd, tmp_path / "crowd.png")
