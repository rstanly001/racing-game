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

import numpy as np

from racing import __version__
from racing.config import PHYSICS_DT, SCREEN_HEIGHT, SCREEN_WIDTH, VehicleSpec
from racing.entities.player import PlayerCar
from racing.entities.vehicle import Vehicle
from racing.exceptions import RacingError

logger = logging.getLogger(__name__)

DEFAULT_LAPS = 3
DEFAULT_TRACK = "oval"
TRACK_CHOICES = ["oval", "figure_eight", "random"]

# Never advance more than this much simulated time in one frame, so a stall
# cannot make the car teleport once the process catches up.
MAX_FRAME_TIME = 0.25


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
        description="A 2D racing game with physics, an AI opponent, and telemetry.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug logging"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    race = subparsers.add_parser("race", help="play interactively against the AI")
    race.add_argument("--track", choices=TRACK_CHOICES, default=DEFAULT_TRACK)
    race.add_argument("--laps", type=int, default=DEFAULT_LAPS)
    race.add_argument("--no-sound", action="store_true")
    race.add_argument("--seed", type=int, default=42)

    simulate = subparsers.add_parser(
        "simulate", help="run a headless AI-vs-AI race and save telemetry"
    )
    simulate.add_argument("--track", choices=TRACK_CHOICES, default=DEFAULT_TRACK)
    simulate.add_argument("--laps", type=int, default=DEFAULT_LAPS)
    simulate.add_argument("--seed", type=int, default=42)
    simulate.add_argument("--output", default="output/telemetry.csv")

    analyze = subparsers.add_parser(
        "analyze", help="read a telemetry file and write analysis plots"
    )
    analyze.add_argument("--input", default="output/telemetry.csv")
    analyze.add_argument("--output-dir", default="output")

    replay = subparsers.add_parser("replay", help="re-render a saved telemetry file")
    replay.add_argument("--input", default="output/telemetry.csv")
    replay.add_argument("--speed", type=float, default=1.0)

    return parser


def direction(vector: np.ndarray) -> np.ndarray:
    """Return the unit vector along ``vector``, or zeros if it has no length."""
    length = float(np.linalg.norm(vector))
    return vector / length if length else np.zeros(2)


def step_car(car: Vehicle, dt: float) -> None:
    """Advance one car by a single physics timestep.

    A stand-in for :class:`~racing.physics.engine.PhysicsEngine`, which takes
    over once there is a track to collide with.

    Parameters
    ----------
    car
        The vehicle to advance. Its controls must already be set.
    dt
        Timestep in seconds.
    """
    spec = car.spec

    # A stationary car cannot steer; the wheels need something to push against.
    if car.speed > 1.0:
        car.heading += car.steering * spec.turn_rate * dt

    car.apply_force(car.forward * spec.acceleration * car.throttle, dt)

    if car.brake and car.speed:
        # Braking may not push the car backwards, so cap it at a full stop.
        car.velocity -= direction(car.velocity) * min(
            spec.brake_force * car.brake * dt, car.speed
        )

    car.apply_grip(spec.grip)
    car.velocity *= max(0.0, 1.0 - spec.drag * dt)

    if car.speed > spec.max_speed:
        car.velocity = direction(car.velocity) * spec.max_speed

    car.integrate(dt)


def command_race(args: argparse.Namespace) -> int:
    """Run the interactive game."""
    # Imported here so that pygame's display code is only touched by the one
    # command that needs a window.
    from racing.game.renderer import Renderer

    car = PlayerCar(
        VehicleSpec(name="Red"),
        position=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2),
    )
    logger.info("Arrow keys to drive, Esc to quit.")

    with Renderer(caption=f"Racing — {car.name}") as renderer:
        pending = 0.0
        while renderer.poll_events():
            pending = min(pending + renderer.tick(), MAX_FRAME_TIME)
            keys = renderer.pressed_keys()

            # The physics runs at a fixed rate whatever the frame rate is.
            while pending >= PHYSICS_DT:
                car.update_controls(PHYSICS_DT, keys=keys)
                step_car(car, PHYSICS_DT)
                pending -= PHYSICS_DT

            renderer.draw([car])

    return 0


def command_simulate(args: argparse.Namespace) -> int:
    """Run a headless AI-vs-AI race and write telemetry to CSV."""
    force_headless()
    # TODO: build the track, two AICars with different aggression values,
    #       Race(...).run(), then write the telemetry and print a summary
    raise NotImplementedError


def command_analyze(args: argparse.Namespace) -> int:
    """Load telemetry, print summaries, and write every plot."""
    # TODO: implement with racing.telemetry.analysis and racing.viz.plots
    raise NotImplementedError


def command_replay(args: argparse.Namespace) -> int:
    """Re-render a saved race from its telemetry."""
    # TODO: implement
    raise NotImplementedError


COMMANDS = {
    "race": command_race,
    "simulate": command_simulate,
    "analyze": command_analyze,
    "replay": command_replay,
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
