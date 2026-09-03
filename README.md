# Racing

A 2D top-down racing game with a physics engine and lap timing, written as
an installable Python package.

The simulation is kept separate from the rendering: a race is stepped at a
fixed rate that has nothing to do with the frame rate, which is what will
later let the same race run with no window at all.

Final project for *Introduction to Python*, TU Dortmund.

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/rstanly001/racing-game.git
cd racing-game
uv pip install -e .
```

## Usage

```bash
uv run -m racing --help
uv run -m racing race --track oval --laps 3
```

| Key | Action |
| --- | --- |
| Up | Throttle |
| Down | Brake |
| Left / Right | Steer |
| Esc | Quit |

The panel in the corner shows the lap counter, speed, last and best lap
times, and elapsed race time. The finishing order is printed on exit.

## Status

This is a project under construction, and the sections below describe only
what is built. Working today:

- Fixed-timestep physics: acceleration, braking, lateral grip and drag,
  advancing at 60 Hz whatever the frame rate does
- Steering that scales with speed, so a standing car cannot turn at all and
  a car near its top speed gives up part of its turn rate
- An oval circuit drawn with kerbs and a chequered start line
- Lap counting over checkpoints that have to be crossed in order, with lap
  times and a finishing order

Not built yet: track boundaries, the computer-controlled opponent, sound,
telemetry recording, and the analysis plots. The `simulate`, `analyze` and
`replay` subcommands are placeholders until those land.

## Using the package as a library

Everything is exported from the top-level package, so the physics and the
track can be driven without the game:

```python
from racing import PhysicsEngine, PlayerCar, VehicleSpec
from racing.track import build_oval

track = build_oval()
car = PlayerCar(VehicleSpec(name="Red"), track, position=tuple(track.start_position))
engine = PhysicsEngine(track)

for _ in range(120):  # two seconds of full throttle
    car.update_controls(engine.dt, keys={"up"})
    engine.step([car])

print(f"{car.speed:.0f} px/s, {track.lap_distance(car.position):.0f} px around")
```

A whole race, with lap counting, runs through `Race`. Any driver that can
produce a set of key names will do — here, one that chases a point further
along the centre line:

```python
import numpy as np

from racing import GameConfig, PlayerCar, Race, VehicleSpec
from racing.track import build_oval

track = build_oval()
car = PlayerCar(VehicleSpec(name="Red"), track)
race = Race(track, [car], GameConfig(laps=2))


def follow_the_line(car):
    """Return the keys needed to head for a point further around the lap."""
    ahead = track.centre_line[(track.nearest_index(car.position) + 12) % len(track)]
    step = ahead - car.position
    wanted = np.degrees(np.arctan2(step[0], -step[1])) % 360.0
    error = (wanted - car.heading + 180.0) % 360.0 - 180.0
    return {"up"} | ({"right"} if error > 3 else {"left"} if error < -3 else set())


while not race.is_complete() and race.time < 60.0:
    race.step(keys=follow_the_line(car))

print(f"{car.lap} laps, best {car.best_lap:.2f}s")
```

## Design notes

**Vehicles sit behind an abstract base class.** `Vehicle` extends
`PhysicsBody` and declares one abstract method, `update_controls`.
`PlayerCar` implements it by reading a set of key names — it never imports
pygame, so it can be driven from a test. The physics engine only ever sees
the abstract interface, so another controller costs one subclass.

**Handling is tuned through `VehicleSpec`, not through the physics code.**
Drag and acceleration together settle the car just under its top speed, so
`max_speed` is a safety net rather than a wall it slams into. Grip is the
fraction of sideways velocity shed per second, raised to the timestep, so it
means the same thing however often the engine steps.

**Laps are counted by checkpoints, in order.** A car is offered every
checkpoint it passes near, but accepts only the one it is due to cross next,
so a lap cannot be claimed by reversing over the line or by cutting the
corner a checkpoint sits behind.

**The scenery is painted once.** The track, its kerbs and the start line go
onto their own surface and are blitted from then on; redrawing several
hundred segments every frame would cost more than the cars do.

## Project structure

```
src/racing/
├── __init__.py        public API
├── __main__.py        module entry point
├── cli.py             argparse subcommands
├── config.py          tuning constants, VehicleSpec, GameConfig
├── exceptions.py      exception hierarchy
├── physics/           PhysicsBody, PhysicsEngine
├── entities/          Vehicle ABC, PlayerCar, AICar
├── track/             Track geometry, procedural generation
├── game/              Race loop, Renderer, AudioManager
├── telemetry/         per-frame recording, pandas analysis
└── viz/               matplotlib figures
```

## Development

```bash
uv pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

The test suite runs entirely headless and never opens a window.

## License

MIT
