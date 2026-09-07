"""Track geometry and procedural generation."""

from racing.track.builder import BUILDERS, build_figure_eight, build_oval
from racing.track.track import Track

__all__ = ["BUILDERS", "Track", "build_figure_eight", "build_oval"]
