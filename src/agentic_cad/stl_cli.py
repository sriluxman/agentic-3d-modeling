from __future__ import annotations

import argparse
from pathlib import Path

from .stl_runner import evaluate_stl


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate and slice an existing STL")
    parser.add_argument("stl", type=Path)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("exports/stl"))
    parser.add_argument("--expected-bodies", type=int, default=1)
    parser.add_argument("--process-preset")
    parser.add_argument("--skip-slicer", action="store_true")
    args = parser.parse_args()

    report_path, report = evaluate_stl(
        args.stl,
        args.profile,
        args.output,
        expected_bodies=args.expected_bodies,
        enable_slicer=not args.skip_slicer,
        process_preset_project_relative=args.process_preset,
    )
    print(f"{report['status'].upper()}: {report_path}")
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
