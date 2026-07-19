from __future__ import annotations

import argparse
from pathlib import Path

from .runner import run
from .study import parse_value


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and evaluate a Python CAD model")
    parser.add_argument("model", type=Path)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("exports/python"))
    parser.add_argument("--skip-slicer", action="store_true")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--skip-freecad", action="store_true")
    parser.add_argument("--png", action="store_true", help="Rasterize SVG renders with a local headless browser")
    parser.add_argument(
        "--set",
        dest="assignments",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Parameter override passed to build_design(profile, overrides=...)",
    )
    args = parser.parse_args()

    overrides = {}
    for assignment in args.assignments:
        name, _, value = assignment.partition("=")
        if not name or not value:
            parser.error(f"Expected NAME=VALUE, got: {assignment}")
        overrides[name.strip()] = parse_value(value)

    report_path, report = run(
        args.model,
        args.profile,
        args.output,
        enable_slicer=not args.skip_slicer,
        enable_render=not args.skip_render,
        enable_freecad=not args.skip_freecad,
        enable_raster=args.png,
        overrides=overrides or None,
    )
    print(f"{report['status'].upper()}: {report_path}")
    if "html_report" in report:
        print(f"review: {report['html_report']}")
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
