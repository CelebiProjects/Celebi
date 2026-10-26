"""Generate independent, reproducible Gaussian pseudoexperiments."""
import argparse
import json
import math
from pathlib import Path
import random


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toys", type=int, default=100)
    parser.add_argument("--events", type=int, default=1000)
    parser.add_argument("--mean", type=float, default=5.0)
    parser.add_argument("--sigma", type=float, default=1.5)
    parser.add_argument("--seed", type=int, default=20261025)
    parser.add_argument("--output", type=Path, default=Path("stageout"))
    args = parser.parse_args()
    if args.toys < 1 or args.events < 3:
        parser.error("toys must be positive and events must be at least 3")
    if not math.isfinite(args.mean) or not math.isfinite(args.sigma) or args.sigma <= 0:
        parser.error("mean and sigma must be finite, with sigma positive")
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "toys": args.toys, "events_per_toy": args.events,
        "truth": {"mean": args.mean, "sigma": args.sigma}, "seed": args.seed, "files": [],
    }
    for index in range(args.toys):
        rng = random.Random(args.seed + index)
        payload = {
            "index": index, "seed": args.seed + index, "truth": manifest["truth"],
            "values": [rng.gauss(args.mean, args.sigma) for _ in range(args.events)],
        }
        relative = f"{index}/toy.json"
        (args.output / str(index)).mkdir(parents=True, exist_ok=True)
        (args.output / relative).write_text(json.dumps(payload, allow_nan=False) + "\n")
        manifest["files"].append(relative)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Generated {args.toys} Gaussian toys, {args.events} events each")


if __name__ == "__main__":
    main()
