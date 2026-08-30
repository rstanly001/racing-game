# Racing

A 2D top-down racing game with a real physics engine, an AI opponent, and a
telemetry system that records every frame of a race and turns it into
analysis plots.

The game can be played interactively, or simulated headlessly with no window
at all — which means the analysis works on any machine, with or without a
display.

Final project for *Introduction to Python*, TU Dortmund.

## Status

Under active development. Working today:

- Fixed-timestep physics: acceleration, braking, lateral grip, and drag,
  advancing at 60 Hz regardless of the frame rate
- Steering that scales with speed. A standing car cannot turn at all, and a
  car near its top speed gives up part of its turn rate, so the oval's
  corners cannot be taken flat out
- Keyboard driving, with steering that ramps in instead of snapping to lock
- An oval circuit drawn with kerbs and a chequered start line

Still to come: boundaries that push a car back onto the track, the AI
opponent, lap timing, telemetry recording, and the analysis plots. Until
those land, leaving the circuit costs you nothing, and `simulate`,
`analyze`, and `replay` are not yet wired up.

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
uv run -m racing simulate --track oval --laps 3 --seed 42
uv run -m racing analyze --input output/telemetry.csv
uv run -m racing race --track oval --laps 3
uv run -m racing replay --input output/telemetry.csv
```

| Command | What it does | Needs a display |
| --- | --- | --- |
| `simulate` | Runs an AI-vs-AI race with no window, writes telemetry to CSV | No |
| `analyze` | Reads telemetry, prints lap summaries, writes plots | No |
| `race` | Interactive game: you against the AI, with sound | Yes |
| `replay` | Re-renders a saved race from its telemetry | Yes |

Start with `simulate` followed by `analyze` — together they exercise the
whole package and produce every figure without needing a screen.

### Controls

| Key | Action |
| --- | --- |
| Up | Throttle |
| Down | Brake |
| Left / Right | Steer |
| Esc | Quit |

## Generated output

No figure is ever displayed interactively; the Agg backend is selected before
pyplot is imported, and every plot is written to disk.

| File | Contents |
| --- | --- |
| `output/telemetry.csv` | Per-frame recording: position, speed, inputs, lap |
| `output/speed_trace.png` | Both cars' speed against lap distance, best laps |
| `output/racing_line.png` | The path each car drove, coloured by speed |
| `output/lap_times.png` | Lap time by lap number, one line per car |
| `output/inputs.png` | Throttle, brake, and steering traces over one lap |

These files are committed to the repository.

## Using the package as a library

```python
from racing import AICar, GameConfig, Race, VehicleSpec
from racing.track import build_oval
from racing.telemetry import lap_summary
from racing.viz import plot_all

track = build_oval()
spec = VehicleSpec(name="Red", max_speed=420.0, grip=0.99)
cars = [
    AICar(spec, track, position=tuple(track.start_position), aggression=0.85),
    AICar(spec, track, position=tuple(track.start_position), aggression=0.70),
]

result = Race(track, cars, GameConfig(laps=3, headless=True)).run()
telemetry = result.to_frame()

print(lap_summary(telemetry))
plot_all(telemetry, "output")
```

See `notebooks/demo.ipynb` for a worked example.

## Design notes

**Vehicles sit behind an abstract base class.** `Vehicle` extends
`PhysicsBody` and declares one abstract method, `update_controls`.
`PlayerCar` implements it by reading the keyboard; `AICar` implements it by
following the racing line. The physics engine only ever sees the abstract
interface, so a new controller — a replay driver, a recorded ghost — costs
one subclass and changes nothing else.

**The simulation is completely separate from rendering.** `Race.step()`
advances the physics at a fixed timestep and knows nothing about pygame.
`Renderer` is imported only by the interactive command. That separation is
what makes `simulate` possible, and it means the physics is deterministic:
the same seed produces the same race every time, regardless of frame rate.

**Audio fails soft.** `AudioManager` catches mixer initialisation failure and
degrades to silence rather than crashing, which is the normal case on a
machine with no sound device.

**Handling is tuned through `VehicleSpec`, not through the physics code.**
Drag and acceleration together settle the car just under its top speed, so
`max_speed` is a safety net rather than a wall it slams into, and the last
tenth of the speedometer has to be earned. Grip is the fraction of sideways
velocity shed per second, raised to the timestep, so it means the same thing
however often the engine steps.

**Telemetry accumulates as plain dicts.** Rows are collected in a list and
converted to a DataFrame once at the end. Appending to a DataFrame per frame
would dominate the runtime.

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
└── viz/               matplotlib figures (Agg, saved to file)
```

## Development

```bash
ruff check .
ruff format .
pytest
```

The test suite runs entirely headless and never opens a window.

## License

MIT
