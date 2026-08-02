"""Pygame rendering.

This module is the only place that draws to a screen. It is imported lazily
by the interactive command, so a headless run never touches the display
subsystem at all.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

import pygame

from racing.config import (
    CAR_LENGTH,
    CAR_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TARGET_FPS,
)
from racing.exceptions import AssetLoadError

if TYPE_CHECKING:
    from racing.entities.vehicle import Vehicle
    from racing.game.race import Race
    from racing.track.track import Track

logger = logging.getLogger(__name__)

GRASS = (32, 92, 48)
ASPHALT = (58, 58, 62)
KERB = (210, 210, 215)
TEXT = (240, 240, 240)
NOSE = (245, 245, 245)

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

    Examples
    --------
    The renderer is a context manager, so the window is always closed even
    if the frame loop raises::

        with Renderer() as renderer:
            while renderer.poll_events():
                renderer.draw(cars)
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
        self._sprites: dict[tuple[int, int, int], pygame.Surface] = {}

    def open(self) -> None:
        """Initialise pygame and create the window.

        Raises
        ------
        AssetLoadError
            If no display is available.
        """
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
        except pygame.error as exc:  # pragma: no cover - needs a broken display
            raise AssetLoadError(f"could not open a window: {exc}") from exc

        pygame.display.set_caption(self.caption)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 26)
        logger.debug("opened a %d×%d window", self.width, self.height)

    def close(self) -> None:
        """Shut pygame down cleanly."""
        self.screen = None
        self.clock = None
        self.font = None
        self._sprites.clear()
        pygame.quit()
        logger.debug("closed the window")

    def poll_events(self) -> bool:
        """Drain the event queue and report whether the game should continue.

        Returns
        -------
        bool
            ``False`` once the window is closed or Esc is pressed.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def pressed_keys(self) -> set[str]:
        """Return the names of currently pressed control keys."""
        pressed = pygame.key.get_pressed()
        return {name for code, name in KEY_NAMES.items() if pressed[code]}

    def draw_track(self, track: Track) -> None:
        """Draw the track surface, its boundaries, and the start line."""
        # TODO: implement
        raise NotImplementedError

    def draw_cars(self, cars: Sequence[Vehicle]) -> None:
        """Draw every car as a rotated rectangle in its own colour.

        Parameters
        ----------
        cars
            The vehicles to draw.
        """
        for car in cars:
            # Sprites are drawn nose-up, and headings run clockwise, so the
            # rotation is negated to match pygame's counter-clockwise angles.
            sprite = pygame.transform.rotate(
                self._sprite(car.spec.colour), -car.heading
            )
            centre = (int(car.position[0]), int(car.position[1]))
            self._surface().blit(sprite, sprite.get_rect(center=centre))

    def draw_hud(self, race: Race) -> None:
        """Draw lap counter, speed, and lap times."""
        # TODO: implement
        raise NotImplementedError

    def draw(self, cars: Sequence[Vehicle]) -> None:
        """Draw one complete frame and flip the display."""
        self._surface().fill(GRASS)
        self.draw_cars(cars)
        pygame.display.flip()

    def tick(self) -> float:
        """Limit the frame rate and return elapsed seconds since last call."""
        if self.clock is None:
            raise AssetLoadError("the renderer is not open")
        return self.clock.tick(TARGET_FPS) / 1000.0

    def _surface(self) -> pygame.Surface:
        """Return the window surface, or complain that it is not open yet."""
        if self.screen is None:
            raise AssetLoadError("the renderer is not open")
        return self.screen

    def _sprite(self, colour: tuple[int, int, int]) -> pygame.Surface:
        """Return the car sprite for ``colour``, building it once per colour."""
        if colour not in self._sprites:
            sprite = pygame.Surface((CAR_WIDTH, CAR_LENGTH), pygame.SRCALPHA)
            sprite.fill(colour)
            # A pale strip at the nose, so the heading is readable at a glance.
            pygame.draw.rect(sprite, NOSE, (0, 0, CAR_WIDTH, CAR_LENGTH * 0.22))
            self._sprites[colour] = sprite
        return self._sprites[colour]

    def __enter__(self) -> Renderer:
        """Open the window on entering a ``with`` block."""
        self.open()
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Close the window on leaving a ``with`` block, even on error."""
        self.close()
