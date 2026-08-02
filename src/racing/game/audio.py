"""Sound effects.

Audio is optional and always fails soft: if the mixer cannot be initialised,
which is normal on a headless machine, every method becomes a no-op and the
game continues silently rather than crashing.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ASSET_DIR = Path(__file__).resolve().parents[3] / "assets" / "sounds"


class AudioManager:
    """Plays engine and collision sounds.

    Parameters
    ----------
    enabled
        Set ``False`` to disable audio entirely, as in a headless run.

    Attributes
    ----------
    available : bool
        Whether the mixer initialised successfully. When ``False``, every
        method returns immediately.
    """

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.available = False
        self._sounds: dict[str, object] = {}

    def open(self) -> None:
        """Initialise the mixer, tolerating failure on headless machines."""
        # TODO: try pygame.mixer.init(); on failure log a warning and leave
        #       self.available as False
        raise NotImplementedError

    def load(self, name: str, filename: str) -> None:
        """Load one sound file under a short name.

        Raises
        ------
        AssetLoadError
            If the file exists but cannot be decoded.
        """
        # TODO: implement; a missing file should warn, not crash
        raise NotImplementedError

    def play(self, name: str) -> None:
        """Play a loaded sound once, if audio is available."""
        # TODO: implement
        raise NotImplementedError

    def engine_pitch(self, speed: float, max_speed: float) -> None:
        """Adjust the looping engine sound to match the current speed."""
        # TODO: implement
        raise NotImplementedError

    def close(self) -> None:
        """Stop all audio and shut the mixer down."""
        # TODO: implement
        raise NotImplementedError
