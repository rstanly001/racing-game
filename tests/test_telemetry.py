"""Tests for telemetry recording and analysis."""

from racing import ComputerCar, Telemetry
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
