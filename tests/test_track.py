"""Tests for track geometry."""

import numpy as np
import pytest

from racing import Track, TrackError
from racing.track import build_oval


def test_centre_of_track_is_inside(track: Track) -> None:
    assert track.contains(track.centre_line[0])


def test_far_away_point_is_outside(track: Track) -> None:
    assert not track.contains(np.array([0.0, 0.0]))


def test_nearest_index_finds_itself(track: Track) -> None:
    assert track.nearest_index(track.centre_line[10]) == 10


def test_checkpoint_count(track: Track) -> None:
    assert len(track.checkpoints) == track.n_checkpoints


def test_checkpoints_start_on_the_start_line(track: Track) -> None:
    assert track.checkpoints[0] == pytest.approx(track.start_position)


def test_racing_line_has_two_columns(track: Track) -> None:
    assert track.racing_line.shape[1] == 2


def test_distance_to_the_centre_line_is_zero(track: Track) -> None:
    assert track.distance_from_centre(track.centre_line[7]) == pytest.approx(0.0)


def test_a_point_between_nodes_is_still_on_the_line(track: Track) -> None:
    midpoint = (track.centre_line[0] + track.centre_line[1]) / 2
    assert track.distance_from_centre(midpoint) < 1.0


def test_the_edge_is_half_a_width_from_the_centre(track: Track) -> None:
    # Only approximately: the centre line is a polyline, so on the inside of
    # a corner its chords cut fractionally inside the curve they sample.
    left, right = track.boundaries()
    half = track.width / 2
    assert track.distance_from_centre(left[0]) == pytest.approx(half, abs=0.1)
    assert track.distance_from_centre(right[0]) == pytest.approx(half, abs=0.1)


def test_just_outside_the_edge_is_off_track(track: Track) -> None:
    left, _ = track.boundaries()
    outward = left[0] - track.centre_line[0]
    assert not track.contains(track.centre_line[0] + outward * 1.01)


def test_tangents_are_unit_vectors(track: Track) -> None:
    assert np.linalg.norm(track.tangents(), axis=1) == pytest.approx(1.0)


def test_normals_are_perpendicular_to_tangents(track: Track) -> None:
    dots = np.einsum("ij,ij->i", track.tangents(), track.normals())
    assert dots == pytest.approx(0.0, abs=1e-9)


def test_start_heading_follows_the_first_segment() -> None:
    # Three nodes, the first segment heading due east.
    line = np.array([[0.0, 0.0], [100.0, 0.0], [50.0, 100.0]])
    triangle = Track("Triangle", line, n_checkpoints=3)
    assert triangle.start_heading == pytest.approx(90.0)


def test_iteration_and_length_agree(track: Track) -> None:
    assert len(list(track)) == len(track)


def test_oval_has_the_requested_node_count() -> None:
    assert len(build_oval(n_points=90)) == 90


def test_oval_closes_on_itself() -> None:
    track = build_oval(n_points=90)
    first_gap = np.linalg.norm(track.centre_line[1] - track.centre_line[0])
    closing_gap = np.linalg.norm(track.centre_line[0] - track.centre_line[-1])
    assert closing_gap == pytest.approx(first_gap, rel=0.05)


def test_a_lap_of_the_oval_stays_on_track() -> None:
    track = build_oval()
    assert all(track.contains(node) for node in track)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"centre_line": np.zeros((4, 3))}, "shape"),
        ({"centre_line": np.zeros((2, 2))}, "at least"),
        ({"width": 0.0}, "width"),
        ({"n_checkpoints": 999}, "n_checkpoints"),
    ],
)
def test_invalid_tracks_are_rejected(kwargs: dict, message: str) -> None:
    defaults = {
        "centre_line": np.array([[0.0, 0.0], [10.0, 0.0], [5.0, 10.0]]),
        "n_checkpoints": 3,
    }
    with pytest.raises(TrackError, match=message):
        Track("Bad", **{**defaults, **kwargs})


def test_the_start_line_is_at_zero_lap_distance(track: Track) -> None:
    assert track.lap_distance(track.start_position) == pytest.approx(0.0)


def test_lap_distance_grows_around_the_lap(track: Track) -> None:
    distances = [track.lap_distance(node) for node in track]
    assert distances == sorted(distances)


def test_lap_distance_never_exceeds_a_lap(track: Track) -> None:
    assert max(track.lap_distance(node) for node in track) < track.lap_length


def test_lap_length_matches_the_summed_segments(track: Track) -> None:
    assert track.lap_length == pytest.approx(track.segment_lengths.sum())


def test_an_oval_is_about_as_long_as_its_ellipse() -> None:
    # Ramanujan's approximation for the perimeter of an ellipse.
    a, b = 440.0, 240.0
    h = (a - b) ** 2 / (a + b) ** 2
    perimeter = np.pi * (a + b) * (1 + 3 * h / (10 + np.sqrt(4 - 3 * h)))
    assert build_oval().lap_length == pytest.approx(perimeter, rel=1e-3)


def test_a_point_off_track_still_has_a_lap_distance(track: Track) -> None:
    outside = track.centre_line[20] * 1.5
    assert 0.0 <= track.lap_distance(outside) <= track.lap_length


def test_the_racing_line_stays_on_the_track(track: Track) -> None:
    assert all(track.contains(point) for point in track.racing_line)


def test_the_racing_line_leaves_room_for_the_car(track: Track) -> None:
    from racing.config import CAR_WIDTH

    room = track.width / 2 - CAR_WIDTH / 2
    assert max(track.distance_from_centre(p) for p in track.racing_line) <= room


def test_the_racing_line_cuts_inside_the_corners(track: Track) -> None:
    # An ellipse bends most at the ends of its long axis, so that is where
    # the line should have moved furthest from the centre line.
    line = track.racing_line
    moved = np.linalg.norm(line - track.centre_line, axis=1)
    assert moved.max() > 1.0


def test_the_racing_line_is_shorter_than_the_centre_line(track: Track) -> None:
    def length(points: np.ndarray) -> float:
        return float(np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1).sum())

    assert length(track.racing_line) < length(track.centre_line)


def test_the_racing_line_has_no_kink_at_the_start_line(track: Track) -> None:
    # It is a closed loop, so the smoothing has to wrap rather than truncate.
    line = track.racing_line
    steps = np.linalg.norm(np.diff(line, axis=0, append=line[:1]), axis=1)
    assert steps.max() < 3 * steps.mean()
