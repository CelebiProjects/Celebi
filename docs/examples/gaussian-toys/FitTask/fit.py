"""Fit one untruncated Gaussian toy using its exact unbinned ML solution."""
import argparse
import json
import math
from pathlib import Path
import statistics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("stageout/index"))
    args = parser.parse_args()
    toy = json.loads(args.input.read_text())
    if toy["index"] != args.index:
        parser.error("input toy index does not match the subtask index")
    values = toy["values"]
    if len(values) < 3 or not all(math.isfinite(value) for value in values):
        parser.error("at least three finite observations are required")
    count = len(values)
    mean = statistics.fmean(values)
    # ML uses N, rather than the unbiased sample variance's N - 1.
    sigma = math.sqrt(math.fsum((value - mean) ** 2 for value in values) / count)
    if sigma <= 0:
        parser.error("the Gaussian maximum likelihood estimate has zero width")
    mean_error = sigma / math.sqrt(count)
    sigma_error = sigma / math.sqrt(2 * count)
    result = {
        "index": args.index, "events": count, "seed": toy["seed"],
        "method": "analytic unbinned Gaussian maximum likelihood",
        "status": "success", "truth": toy["truth"],
        "mean": mean, "sigma": sigma, "mean_error": mean_error, "sigma_error": sigma_error,
        "mean_pull": (mean - toy["truth"]["mean"]) / mean_error,
        "sigma_pull": (sigma - toy["truth"]["sigma"]) / sigma_error,
        "negative_log_likelihood": count * (math.log(sigma * math.sqrt(2 * math.pi)) + 0.5),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "fit.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Toy {args.index}: mean={mean:.5f} +/- {mean_error:.5f}, "
          f"sigma={sigma:.5f} +/- {sigma_error:.5f}")


if __name__ == "__main__":
    main()
