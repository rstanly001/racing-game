"""Exception hierarchy for the :mod:`racing` package.

Every error raised by this package inherits from :class:`RacingError`, so a
caller can catch all of them with a single ``except RacingError`` clause.
"""


class RacingError(Exception):
    """Base class for all errors raised by this package."""


class TrackError(RacingError):
    """Raised when a track file is missing, malformed, or invalid."""


class AssetLoadError(RacingError):
    """Raised when a display or an asset cannot be opened."""


class TelemetryError(RacingError):
    """Raised when telemetry is recorded or read back incorrectly."""


class ConfigurationError(RacingError):
    """Raised when the game or a vehicle is configured with bad values."""
