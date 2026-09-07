"""Pygame rendering.

This module is the only place that draws to a screen. It is imported lazily
by the interactive command, so a headless run never touches the display
subsystem at all.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
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
GRASS_DARK = (29, 86, 45)
ASPHALT = (58, 58, 62)
ASPHALT_EDGE = (44, 44, 48)
KERB = (222, 222, 226)
KERB_RED = (192, 58, 50)
LINE_LIGHT = (236, 236, 238)
LINE_DARK = (26, 26, 30)
TEXT = (240, 240, 240)
GLASS = (38, 44, 56)
HEADLIGHT = (250, 244, 205)
TAILLIGHT = (132, 32, 28)

# Widths in pixels of the painted details on the track surface.
GRASS_STRIPE = 96
KERB_DEPTH = 7
KERB_SEGMENTS = 3
START_LINE_DEPTH = 9
START_LINE_SQUARES = 8

# Heads-up display: a panel of readings in the top-left corner.
HUD_PANEL = (18, 18, 22, 190)
HUD_LABEL = (150, 152, 160)
HUD_WIDTH = 190
HUD_MARGIN = 16
HUD_PADDING = 12
HUD_LINE_HEIGHT = 26
HUD_TEXT_SIZE = 26
HUD_BANNER_SIZE = 96

KEY_NAMES = {
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
}


def _point(position: np.ndarray) -> tuple[int, int]:
    """Return a position rounded to whole pixels, as pygame wants it."""
    return int(position[0]), int(position[1])


def _lap_time(seconds: float | None) -> str:
    """Return a lap time as ``m:ss.hh``, or dashes if there isn't one yet."""
    if seconds is None:
        return "--:--"
    minutes, remainder = divmod(seconds, 60)
    return f"{int(minutes)}:{remainder:05.2f}"


def _shade(colour: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """Return ``colour`` darkened or lightened by ``factor``."""
    return tuple(min(255, max(0, int(channel * factor))) for channel in colour)


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
                renderer.draw(race)
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
        self._scenery: pygame.Surface | None = None
        self._scenery_of: Track | None = None

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
        self.font = pygame.font.Font(None, HUD_TEXT_SIZE)
        logger.debug("opened a %d×%d window", self.width, self.height)

    def close(self) -> None:
        """Shut pygame down cleanly."""
        self.screen = None
        self.clock = None
        self.font = None
        self._sprites.clear()
        self._scenery = None
        self._scenery_of = None
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
        """Draw the track surface, its kerbs, and the start line.

        Nothing about the scenery moves, so it is painted once onto its own
        surface and blitted from then on. Redrawing several hundred segments
        every frame would cost more than the cars do.
        """
        if self._scenery is None or self._scenery_of is not track:
            self._scenery = self._paint_scenery(track)
            self._scenery_of = track
            logger.debug("painted the scenery for %r", track.name)

        self._surface().blit(self._scenery, (0, 0))

    def _paint_scenery(self, track: Track) -> pygame.Surface:
        """Render the grass, the asphalt, the kerbs, and the start line."""
        scenery = pygame.Surface((self.width, self.height))
        scenery.fill(GRASS)

        # Mown stripes: without them the infield is a flat green void, and a
        # car crossing it has nothing to move against.
        for x in range(0, self.width, 2 * GRASS_STRIPE):
            pygame.draw.rect(scenery, GRASS_DARK, (x, 0, GRASS_STRIPE, self.height))

        left, right = track.boundaries()
        self._paint_asphalt(scenery, track)
        self._paint_kerb(scenery, left)
        self._paint_kerb(scenery, right)
        self._paint_start_line(scenery, track, left[0], right[0])
        return scenery

    def _paint_asphalt(self, scenery: pygame.Surface, track: Track) -> None:
        """Lay a band of asphalt along the centre line.

        Drawn as one thick segment per pair of nodes, with a disc at each
        node to fill the wedge that consecutive segments leave open. Doing it
        this way keeps the seams closed on a track that crosses itself, which
        a single filled polygon could not.
        """
        radius = int(track.width / 2)
        nodes = [(int(x), int(y)) for x, y in track.centre_line]

        for colour, width in ((ASPHALT_EDGE, radius * 2 + 4), (ASPHALT, radius * 2)):
            for start, end in zip(nodes, nodes[1:] + nodes[:1], strict=True):
                pygame.draw.line(scenery, colour, start, end, width)
            for node in nodes:
                pygame.draw.circle(scenery, colour, node, width // 2)

    def _paint_kerb(self, scenery: pygame.Surface, edge: np.ndarray) -> None:
        """Paint an alternating red and white kerb along one track edge."""
        points = [(int(x), int(y)) for x, y in edge]

        edges = zip(points, points[1:] + points[:1], strict=True)
        for index, (start, end) in enumerate(edges):
            colour = KERB if (index // KERB_SEGMENTS) % 2 == 0 else KERB_RED
            pygame.draw.line(scenery, colour, start, end, KERB_DEPTH)

    def _paint_start_line(
        self,
        scenery: pygame.Surface,
        track: Track,
        left: np.ndarray,
        right: np.ndarray,
    ) -> None:
        """Paint a chequered band across the track at the start line."""
        across = (right - left) / START_LINE_SQUARES
        along = track.tangents()[0] * (START_LINE_DEPTH / 2)

        for row in (-1, 1):
            for square in range(START_LINE_SQUARES):
                near = left + across * square + along * (row - 1)
                far = near + along * 2
                colour = LINE_LIGHT if (square + row) % 2 else LINE_DARK
                pygame.draw.polygon(
                    scenery,
                    colour,
                    [
                        _point(near),
                        _point(near + across),
                        _point(far + across),
                        _point(far),
                    ],
                )

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
        """Draw the lap counter, speed, and lap times for the leading human.

        With no human in the race, as in a simulated field, the leader is
        shown instead, so the panel is never empty.
        """
        car = next((one for one in race.cars if one.is_human), race.standings[0])
        finished = race.is_complete()

        lines = [
            ("LAP", f"{min(car.lap + 1, race.config.laps)}/{race.config.laps}"),
            ("SPEED", f"{car.speed:.0f}"),
            ("LAST", _lap_time(car.lap_times[-1] if car.lap_times else None)),
            ("BEST", _lap_time(car.best_lap)),
            ("TIME", _lap_time(race.time)),
        ]
        self._draw_panel(lines, banner="FINISHED" if finished else None)

    def _draw_panel(
        self, lines: Sequence[tuple[str, str]], banner: str | None = None
    ) -> None:
        """Draw a translucent panel of label and value pairs, top left."""
        font = self._typeface()
        height = HUD_LINE_HEIGHT * len(lines) + 2 * HUD_PADDING
        panel = pygame.Surface((HUD_WIDTH, height), pygame.SRCALPHA)
        panel.fill(HUD_PANEL)

        for row, (label, value) in enumerate(lines):
            y = HUD_PADDING + row * HUD_LINE_HEIGHT
            panel.blit(font.render(label, True, HUD_LABEL), (HUD_PADDING, y))
            reading = font.render(value, True, TEXT)
            panel.blit(reading, reading.get_rect(topright=(HUD_WIDTH - HUD_PADDING, y)))

        self._surface().blit(panel, (HUD_MARGIN, HUD_MARGIN))

        if banner:
            shout = self._typeface(HUD_BANNER_SIZE).render(banner, True, TEXT)
            centre = (self.width // 2, self.height // 2)
            self._surface().blit(shout, shout.get_rect(center=centre))

    def draw(self, race: Race) -> None:
        """Draw one complete frame and flip the display."""
        self.draw_track(race.track)
        self.draw_cars(race.cars)
        self.draw_hud(race)
        pygame.display.flip()

    def tick(self) -> float:
        """Limit the frame rate and return elapsed seconds since last call."""
        if self.clock is None:
            raise AssetLoadError("the renderer is not open")
        return self.clock.tick(TARGET_FPS) / 1000.0

    def _typeface(self, size: int = HUD_TEXT_SIZE) -> pygame.font.Font:
        """Return the HUD font, or one at another size for the finish banner."""
        if size != HUD_TEXT_SIZE:
            return pygame.font.Font(None, size)
        if self.font is None:
            raise AssetLoadError("the renderer is not open")
        return self.font

    def _surface(self) -> pygame.Surface:
        """Return the window surface, or complain that it is not open yet."""
        if self.screen is None:
            raise AssetLoadError("the renderer is not open")
        return self.screen

    def _sprite(self, colour: tuple[int, int, int]) -> pygame.Surface:
        """Return the car sprite for ``colour``, building it once per colour.

        The car is drawn nose-up, in bands from the front: headlights,
        bonnet, windscreen, roof, rear window, then dim tail lights. The
        bright end and the dim end are what make its heading obvious at
        thirty pixels long.
        """
        if colour in self._sprites:
            return self._sprites[colour]

        length, width = int(CAR_LENGTH), int(CAR_WIDTH)
        tyre = (max(3, width // 5), max(4, length // 4))

        sprite = pygame.Surface((width + 2 * tyre[0], length), pygame.SRCALPHA)
        body = pygame.Rect(tyre[0], 0, width, length)

        def band(top: float, bottom: float, inset: int) -> pygame.Rect:
            """Return a rectangle spanning the car between two length fractions."""
            return pygame.Rect(
                body.left + inset,
                round(length * top),
                body.width - 2 * inset,
                round(length * (bottom - top)),
            )

        for x in (0, body.right):
            for y in (round(length * 0.13), round(length * 0.65)):
                pygame.draw.rect(sprite, LINE_DARK, (x, y, *tyre), border_radius=1)

        pygame.draw.rect(sprite, colour, body, border_radius=4)
        pygame.draw.rect(sprite, _shade(colour, 1.15), band(0.38, 0.64, 1))
        pygame.draw.rect(sprite, GLASS, band(0.24, 0.38, 2), border_radius=1)
        pygame.draw.rect(sprite, GLASS, band(0.64, 0.75, 3), border_radius=1)
        pygame.draw.rect(sprite, _shade(colour, 0.4), body, width=2, border_radius=4)

        lamp = max(3, width // 4)
        for x in (body.left + 2, body.right - 2 - lamp):
            pygame.draw.rect(sprite, HEADLIGHT, (x, body.top + 1, lamp, 3))
            pygame.draw.rect(sprite, TAILLIGHT, (x, body.bottom - 4, lamp, 3))

        self._sprites[colour] = sprite
        return sprite

    def __enter__(self) -> Renderer:
        """Open the window on entering a ``with`` block."""
        self.open()
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Close the window on leaving a ``with`` block, even on error."""
        self.close()
