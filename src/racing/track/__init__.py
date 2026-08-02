"""Track geometry and procedural generation."""

from racing.track.builder import build_figure_eight, build_oval, build_random
from racing.track.track import Track

__all__ = ["Track", "build_figure_eight", "build_oval", "build_random"]
