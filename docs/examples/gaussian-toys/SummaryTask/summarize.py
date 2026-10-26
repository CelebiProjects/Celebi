"""Require all toy fits, then summarize parameter estimates and pulls."""
import argparse
import csv
import json
import math
from pathlib import Path
import statistics


def histogram(values, title, x, y, reference):
    """Draw a dependency-free SVG histogram."""
    width, height, bins = 380, 190, 20
    low, high = min(min(values), reference), max(max(values), reference)
    padding = max((high - low) * 0.1, 0.01)
    low, high = low - padding, high + padding
    counts = [0] * bins
    for value in values:
        bucket = min(bins - 1, int((value - low) / (high - low) * bins))
        counts[bucket] += 1
    lines = [f'<g transform="translate({x},{y})">',
             f'<text x="0" y="-15" font-size="17">{title}</text>',
             f'<path d="M0,0 V{height} H{width}" fill="none" stroke="#475569"/>']
    for bucket, count in enumerate(counts):
        bar_height = count / max(counts) * (height - 15)
        lines.append(
            f'<rect x="{bucket * width / bins:.2f}" y="{height - bar_height:.2f}" '
            f'width="{width / bins - 1:.2f}" height="{bar_height:.2f}" fill="#2563eb"/>')
    position = (reference - low) / (high - low) * width
    lines.append(f'<path d="M{position:.2f},0 V{height}" stroke="#dc2626" '
                 'stroke-width="2" stroke-dasharray="5 4"/>')
    lines.extend([
        f'<text x="0" y="{height + 20}">{low:.3f}</text>',
        f'<text x="{width}" y="{height + 20}" text-anchor="end">{high:.3f}</text>',
        f'<text x="0" y="{height + 42}" font-size="12">'
        f'mean = {statistics.fmean(values):.4f}, std = {statistics.stdev(values):.4f}</text>',
        '</g>',
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fits", type=Path, required=True)
    parser.add_argument("--expected", type=int, default=100)
    parser.add_argument("--output", type=Path, default=Path("stageout"))
    args = parser.parse_args()
    if args.expected < 2:
        parser.error("at least two toys are needed for ensemble summaries")
    expected = {str(index) for index in range(args.expected)}
    found = {item.parent.name for item in args.fits.glob("*/fit.json")}
    if found != expected:
        parser.error(f"incomplete ensemble: missing={sorted(expected - found)}, "
                     f"unexpected={sorted(found - expected)}")
    rows = []
    for index in range(args.expected):
        row = json.loads((args.fits / str(index) / "fit.json").read_text())
        if row["index"] != index or row["status"] != "success":
            parser.error(f"invalid or failed fit at index {index}")
        if rows and (row["truth"] != rows[0]["truth"] or row["events"] != rows[0]["events"]):
            parser.error("all fits must use the same truth and event count")
        rows.append(row)
    summary = {"toys": len(rows), "events_per_toy": rows[0]["events"],
               "truth": rows[0]["truth"], "method": rows[0]["method"], "statistics": {}}
    for key in ("mean", "sigma", "mean_pull", "sigma_pull"):
        values = [row[key] for row in rows]
        if not all(math.isfinite(value) for value in values):
            parser.error(f"non-finite {key} in fit results")
        summary["statistics"][key] = {
            "mean": statistics.fmean(values), "std": statistics.stdev(values),
            "minimum": min(values), "maximum": max(values),
        }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    fields = ["index", "events", "mean", "mean_error", "sigma", "sigma_error",
              "mean_pull", "sigma_pull", "negative_log_likelihood", "status"]
    with (args.output / "fits.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    panels = []
    for key, title, x, y, reference in (
        ("mean", "Fitted Gaussian mean", 60, 90, rows[0]["truth"]["mean"]),
        ("sigma", "Fitted Gaussian sigma", 520, 90, rows[0]["truth"]["sigma"]),
        ("mean_pull", "Mean pull", 60, 390, 0),
        ("sigma_pull", "Sigma pull", 520, 390, 0),
    ):
        panels.append(histogram([row[key] for row in rows], title, x, y, reference))
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="960" height="690" '
           'viewBox="0 0 960 690"><rect width="960" height="690" fill="white"/>'
           '<g font-family="sans-serif" fill="#0f172a">'
           f'<text x="60" y="30" font-size="22">{len(rows)} Gaussian toy fits</text>'
           '<text x="60" y="54" font-size="13">Red dashed lines: truth or zero pull. '
           'Errors use the asymptotic likelihood curvature.</text>'
           + "\n".join(panels) + '</g></svg>\n')
    (args.output / "summary.svg").write_text(svg)
    report = [f"# Gaussian toy ensemble: {len(rows)} successful fits", "",
              f"Events per toy: {rows[0]['events']}",
              f"Generated mean: {rows[0]['truth']['mean']}",
              f"Generated sigma: {rows[0]['truth']['sigma']}", "",
              "| Quantity | Ensemble mean | Ensemble standard deviation |",
              "|---|---:|---:|"]
    for key, values in summary["statistics"].items():
        report.append(f"| {key} | {values['mean']:.6f} | {values['std']:.6f} |")
    report.extend(["", "![Parameter estimates and pulls](summary.svg)", "",
                   "Individual results: [fits.csv](fits.csv).", ""])
    (args.output / "report.md").write_text("\n".join(report))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
