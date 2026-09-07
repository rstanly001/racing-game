"""Tests for the pandas analysis of a telemetry recording.

These run one real headless race and then check the summaries against what
the cars themselves recorded, which is the only ground truth available.
"""

import pandas as pd
import pytest

from racing import ComputerCar, GameConfig, Race, TelemetryError, VehicleSpec
from racing.telemetry import (
    best_lap_of,
    compare_cars,
    fastest_lap,
    lap_summary,
    race_summary,
    sector_times,
)
from racing.track import build_oval

LAPS = 3


@pytest.fixture(scope="module")
def race() -> Race:
    """One finished race, shared by every test in this file."""
    track = build_oval()
    cars = [
        ComputerCar(VehicleSpec(name="Blue"), track, aggression=0.9),
        ComputerCar(VehicleSpec(name="Gold"), track, aggression=0.7),
    ]
    finished = Race(track, cars, GameConfig(laps=LAPS))
    finished.run(max_seconds=120.0)
    return finished


@pytest.fixture(scope="module")
def telemetry(race: Race) -> pd.DataFrame:
    return race.telemetry.to_frame()


def test_lap_times_match_what_the_cars_recorded(race: Race, telemetry) -> None:
    laps = lap_summary(telemetry)

    for car in race.cars:
        derived = laps.loc[car.name, "lap_time"].tolist()
        assert derived == pytest.approx(car.lap_times, abs=1e-9)


def test_one_row_per_completed_lap(race: Race, telemetry) -> None:
    assert len(lap_summary(telemetry)) == LAPS * len(race.cars)


def test_laps_are_numbered_from_one(telemetry) -> None:
    numbers = lap_summary(telemetry).index.get_level_values("lap")
    assert sorted(set(numbers)) == [1, 2, 3]


def test_speeds_are_ordered_sensibly(telemetry) -> None:
    laps = lap_summary(telemetry)
    assert (laps["average_speed"] <= laps["top_speed"]).all()


def test_time_on_the_throttle_fits_inside_the_lap(telemetry) -> None:
    laps = lap_summary(telemetry)
    assert (laps["on_throttle"] <= laps["lap_time"]).all()
    assert (laps["on_brakes"] <= laps["lap_time"]).all()


def test_the_race_summary_ranks_by_total_time(telemetry) -> None:
    summary = race_summary(telemetry)
    assert summary["total_time"].is_monotonic_increasing


def test_the_race_summary_agrees_with_the_lap_summary(telemetry) -> None:
    laps, summary = lap_summary(telemetry), race_summary(telemetry)

    for car in summary.index:
        assert summary.loc[car, "best_lap"] == pytest.approx(
            laps.loc[car, "lap_time"].min()
        )
        assert summary.loc[car, "laps"] == LAPS


def test_the_bolder_driver_comes_out_ahead(telemetry) -> None:
    assert race_summary(telemetry).index[0] == "Blue"


def test_sectors_add_up_to_the_lap(telemetry) -> None:
    # A car starts behind the line, so its opening lap passes through the
    # final sector twice. Timing a sector by its first and last frame used
    # to swallow almost the whole lap.
    sectors = sector_times(telemetry).groupby(level=["car", "lap"])["sector_time"].sum()
    laps = lap_summary(telemetry)["lap_time"]

    assert sectors.reindex(laps.index).to_numpy() == pytest.approx(laps.to_numpy())


def test_every_lap_is_cut_into_the_sectors_asked_for(telemetry) -> None:
    sectors = sector_times(telemetry, n_sectors=4)
    assert sectors.groupby(level=["car", "lap"]).size().eq(4).all()


def test_a_lap_needs_at_least_one_sector(telemetry) -> None:
    with pytest.raises(TelemetryError, match="at least one sector"):
        sector_times(telemetry, n_sectors=0)


def test_the_fastest_lap_is_the_quickest_one(telemetry) -> None:
    laps = lap_summary(telemetry)
    car, lap = laps["lap_time"].idxmin()

    quickest = fastest_lap(telemetry)
    assert set(quickest["car"]) == {car}
    assert set(quickest["lap"]) == {lap}


def test_a_car_best_lap_belongs_to_that_car(telemetry) -> None:
    assert set(best_lap_of(telemetry, "Gold")["car"]) == {"Gold"}


def test_an_unknown_car_is_reported(telemetry) -> None:
    with pytest.raises(TelemetryError, match="no completed laps"):
        best_lap_of(telemetry, "Nobody")


def test_cars_are_compared_on_a_shared_distance_grid(telemetry) -> None:
    comparison = compare_cars(telemetry)

    assert list(comparison.columns) == ["Blue", "Gold"]
    assert comparison.index.name == "lap_distance"
    assert comparison.index.is_monotonic_increasing
    assert not comparison.isna().to_numpy().any()


def test_empty_telemetry_is_reported_rather_than_crashing() -> None:
    from racing.telemetry.recorder import COLUMNS

    with pytest.raises(TelemetryError, match="no telemetry"):
        lap_summary(pd.DataFrame(columns=COLUMNS))
