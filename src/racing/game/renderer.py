"""Pygame rendering.

This module is the only place that draws to a screen. It is imported lazily
by the interactive command, so a headless run never touches the display
subsystem at all.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from racing.config import (  # noqa: F401  (TARGET_FPS used once tick() is implemented)
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TARGET_FPS,
)

if TYPE_CHECKING:
    from racing.game.race import Race
    from racing.track.track import Track

logger = logging.getLogger(__name__)

GRASS = (32, 92, 48)
ASPHALT = (58, 58, 62)
KERB = (210, 210, 215)
TEXT = (240, 240, 240)

KEY_NAMES = {
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
}


class Renderer:
    """Draws the track, the cars, and the heads-up display.

    Parameters
    ----------
    width, height
        Window size in pixels.
    caption
        Window title.
    """

    def __init__(
        self,
        width: int = SCREEN_WIDTH,
        height: int = SCREEN_HEIGHT,
        caption: str = "Racing",
    ) -> None:
        self.width = width
        self.height = height
        self.caption = caption
        self.screen: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.font: pygame.font.Font | None = None

    def open(self) -> None:
        """Initialise pygame and create the window."""
        # TODO: implement
        raise NotImplementedError

    def close(self) -> None:
        """Shut pygame down cleanly."""
        # TODO: implement
        raise NotImplementedError

    def pressed_keys(self) -> set[str]:
        """Return the names of currently pressed control keys."""
        # TODO: implement using KEY_NAMES and pygame.key.get_pressed()
        raise NotImplementedError

    def draw_track(self, track: Track) -> None:
        """Draw the track surface, its boundaries, and the start line."""
        # TODO: implement
        raise NotImplementedError

    def draw_cars(self, race: Race) -> None:
        """Draw every car as a rotated rectangle in its own colour."""
        # TODO: implement with pygame.transform.rotate
        raise NotImplementedError

    def draw_hud(self, race: Race) -> None:
        """Draw lap counter, speed, and lap times."""
        # TODO: implement
        raise NotImplementedError

    def draw(self, race: Race) -> None:
        """Draw one complete frame and flip the display."""
        # TODO: implement
        raise NotImplementedError

    def tick(self) -> float:
        """Limit the frame rate and return elapsed seconds since last call."""
        # TODO: implement
        raise NotImplementedError

    def __enter__(self) -> Renderer:
        """Open the window on entering a ``with`` block."""
        self.open()
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Close the window on leaving a ``with`` block, even on error."""
        self.close()
