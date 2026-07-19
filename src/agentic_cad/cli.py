from __future__ import annotations

import argparse
from pathlib import Path

from .runner import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and evaluate a Python CAD model")
    parser.add_argument("model", type=Path)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("exports/python"))
    parser.add_argument("--skip-slicer", action="store_true")
    args = parser.parse_args()

    report_path, report = run(args.model, args.profile, args.output, enable_slicer=not args.skip_slicer)
    print(f"{report['status'].upper()}: {report_path}")
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
