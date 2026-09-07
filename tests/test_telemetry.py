"""Tests for telemetry recording and analysis."""

import numpy as np
import pytest

from racing import ComputerCar, GameConfig, Race, Telemetry, TelemetryError
from racing.telemetry.recorder import COLUMNS


def test_starts_empty() -> None:
    assert len(Telemetry()) == 0


def test_record_appends_a_row(spec, track) -> None:
    car = ComputerCar(spec, track, position=(0.0, 0.0))
    telemetry = Telemetry()
    telemetry.record(0.0, car, lap_distance=0.0)
    assert len(telemetry) == 1


def test_frame_has_expected_columns(spec, track) -> None:
    car = ComputerCar(spec, track, position=(0.0, 0.0))
    telemetry = Telemetry()
    telemetry.record(0.0, car, lap_distance=0.0)
    assert list(telemetry.to_frame().columns) == COLUMNS


def test_csv_round_trip(tmp_path, spec, track) -> None:
    car = ComputerCar(spec, track, position=(0.0, 0.0))
    telemetry = Telemetry()
    telemetry.record(0.0, car, lap_distance=0.0)
    path = telemetry.to_csv(tmp_path / "telemetry.csv")
    assert len(Telemetry.from_csv(path)) == 1


def test_a_race_records_one_row_per_car_per_step(spec, track) -> None:
    cars = [ComputerCar(spec, track), ComputerCar(spec, track)]
    race = Race(track, cars, GameConfig(laps=1))

    for _ in range(10):
        race.step()

    assert len(race.telemetry) == 20


def test_recording_can_be_switched_off(spec, track) -> None:
    race = Race(track, [ComputerCar(spec, track)], GameConfig(record_telemetry=False))
    race.step()
    assert len(race.telemetry) == 0


def test_rows_carry_where_the_car_was_on_the_lap(spec, track) -> None:
    race = Race(track, [ComputerCar(spec, track)], GameConfig(laps=1))
    race.step()

    row = race.telemetry.to_frame().iloc[0]
    assert row["lap_distance"] == pytest.approx(
        track.lap_distance(race.cars[0].position)
    )


def test_a_collision_is_flagged_on_the_step_it_happened(spec, track) -> None:
    # Overlapping and closing, so the contact lands on the first step. Not
    # exactly coincident: cars sharing a position have no direction to be
    # pushed apart along, and the engine leaves them alone.
    cars = [ComputerCar(spec, track), ComputerCar(spec, track)]
    race = Race(track, cars, GameConfig(laps=1))

    cars[0].position = np.array(track.start_position, dtype=float)
    cars[1].position = cars[0].position + np.array([8.0, 0.0])
    cars[1].velocity = np.array([-200.0, 0.0])

    race.step()
    assert race.telemetry.to_frame()["collision"].any()


def test_a_missing_file_is_reported_as_telemetry_trouble(tmp_path) -> None:
    with pytest.raises(TelemetryError, match="no telemetry file"):
        Telemetry.from_csv(tmp_path / "nothing.csv")


def test_a_file_without_the_right_columns_is_rejected(tmp_path) -> None:
    path = tmp_path / "wrong.csv"
    path.write_text("time,car\n0.0,Red\n", encoding="utf-8")

    with pytest.raises(TelemetryError, match="missing columns"):
        Telemetry.from_csv(path)


def test_an_empty_recording_still_has_the_columns() -> None:
    assert list(Telemetry().to_frame().columns) == COLUMNS
