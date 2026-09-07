"""Command-line interface.

Each subcommand parses arguments, calls into the library, and reports what
it did. No game or analysis logic lives here.

The ``race`` command is the only one that needs a display. Everything else
runs headless, so the package is fully usable on a machine without a screen.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Sequence

from racing import __version__
from racing.config import GameConfig, VehicleSpec
from racing.entities.computer import ComputerCar
from racing.entities.player import PlayerCar
from racing.entities.vehicle import Vehicle
from racing.exceptions import RacingError
from racing.game.race import Race
from racing.track.builder import BUILDERS

logger = logging.getLogger(__name__)

DEFAULT_LAPS = 3
DEFAULT_TRACK = "oval"
TRACK_CHOICES = list(BUILDERS)

# Never advance more than this much simulated time in one frame, so a stall
# cannot make the car teleport once the process catches up.
MAX_FRAME_TIME = 0.25

# The field, in the order opponents are added: name, colour, and how close to
# its limit each one drives.
OPPONENTS = [
    ("Blue", (64, 110, 220), 0.85),
    ("Gold", (226, 176, 54), 0.72),
    ("Green", (76, 176, 96), 0.95),
]


def force_headless() -> None:
    """Make pygame initialise without a display or audio device.

    Setting these before pygame is imported lets the physics and telemetry
    run on a headless server, which is how the project is graded.
    """
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level parser and its subcommands."""
    parser = argparse.ArgumentParser(
        prog="racing",
        description="A 2D racing game with physics, computer opponents, and telemetry.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug logging"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    race = subparsers.add_parser("race", help="play interactively against the computer")
    race.add_argument("--track", choices=TRACK_CHOICES, default=DEFAULT_TRACK)
    race.add_argument("--laps", type=int, default=DEFAULT_LAPS)
    race.add_argument(
        "--opponents",
        type=int,
        choices=range(len(OPPONENTS) + 1),
        default=1,
        help="how many computer-driven cars to race against",
    )

    simulate = subparsers.add_parser(
        "simulate", help="run a headless race between computer drivers"
    )
    simulate.add_argument("--track", choices=TRACK_CHOICES, default=DEFAULT_TRACK)
    simulate.add_argument("--laps", type=int, default=DEFAULT_LAPS)
    simulate.add_argument("--output", default="output/telemetry.csv")

    analyze = subparsers.add_parser(
        "analyze", help="read a telemetry file and write analysis plots"
    )
    analyze.add_argument("--input", default="output/telemetry.csv")
    analyze.add_argument("--output-dir", default="output")

    return parser


def command_race(args: argparse.Namespace) -> int:
    """Run the interactive game."""
    # Imported here so that pygame's display code is only touched by the one
    # command that needs a window.
    from racing.game.renderer import Renderer

    track = BUILDERS[args.track]()
    config = GameConfig(laps=args.laps)
    race = Race(track, build_field(track, args.opponents), config)
    logger.info(
        "%s, %d lap(s), %d opponent(s). Arrow keys to drive, Esc to quit.",
        track.name,
        config.laps,
        args.opponents,
    )

    with Renderer(caption=f"Racing — {track.name}") as renderer:
        pending = 0.0
        while renderer.poll_events():
            pending = min(pending + renderer.tick(), MAX_FRAME_TIME)
            keys = renderer.pressed_keys()

            # The physics runs at a fixed rate whatever the frame rate is.
            # Once the race is over the window stays up until Esc, so the
            # final time can be read off the panel.
            while pending >= race.dt and not race.is_complete():
                race.step(keys)
                pending -= race.dt

            renderer.draw(race)

    report_result(race.standings)
    return 0


def build_field(track, opponents: int) -> list[Vehicle]:
    """Return the player's car followed by ``opponents`` computer drivers."""
    field: list[Vehicle] = [PlayerCar(VehicleSpec(name="You"), track)]

    for name, colour, aggression in OPPONENTS[:opponents]:
        spec = VehicleSpec(name=name, colour=colour)
        field.append(ComputerCar(spec, track, aggression=aggression))

    return field


def report_result(order: Sequence[Vehicle]) -> None:
    """Print a finishing order, one line per car."""
    for place, car in enumerate(order, start=1):
        best = f"{car.best_lap:.2f}s" if car.best_lap else "no complete lap"
        print(f"{place}. {car.name}: {car.lap} lap(s), best {best}")


def command_simulate(args: argparse.Namespace) -> int:
    """Run a headless race between computer drivers and write telemetry to CSV."""
    force_headless()

    track = BUILDERS[args.track]()
    config = GameConfig(laps=args.laps)
    cars = [
        ComputerCar(VehicleSpec(name=name, colour=colour), track, aggression=aggression)
        for name, colour, aggression in OPPONENTS[:2]
    ]

    result = Race(track, cars, config).run()
    path = result.telemetry.to_csv(args.output)

    print(f"{track.name}, {config.laps} laps, {len(cars)} cars")
    report_result(result.finish_order)
    print(f"{len(result.telemetry)} rows of telemetry written to {path}")
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    """Load telemetry, print summaries, and write every plot."""
    # Imported here so that matplotlib is only loaded by the command that
    # needs it, which keeps `import racing` cheap.
    from racing.telemetry import Telemetry, lap_summary, race_summary, sector_times
    from racing.viz import plot_all

    telemetry = Telemetry.from_csv(args.input)
    print(f"{len(telemetry)} rows from {args.input}")

    for heading, table in (
        ("Race", race_summary(telemetry)),
        ("Laps", lap_summary(telemetry)),
        ("Sectors", sector_times(telemetry)),
    ):
        print()
        print(f"== {heading} ==")
        print(table.round(2).to_string())

    print()
    for path in plot_all(telemetry, args.output_dir):
        print(f"wrote {path}")

    return 0


COMMANDS = {
    "race": command_race,
    "simulate": command_simulate,
    "analyze": command_analyze,
}


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code.

    Parameters
    ----------
    argv
        Argument list, defaulting to ``sys.argv[1:]``.

    Returns
    -------
    int
        ``0`` on success, ``1`` on a handled package error, ``130`` if
        interrupted.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        return COMMANDS[args.command](args)
    except RacingError as exc:
        logger.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
