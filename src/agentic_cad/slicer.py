from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any


METRIC_PATTERNS = {
    "layer_count": r"^; total layers count = (\d+)$",
    "max_height_mm": r"^; max_z_height: ([\d.]+)$",
    "filament_length_mm": r"^; filament used \[mm\] = ([\d.]+)$",
    "filament_volume_cm3": r"^; filament used \[cm3\] = ([\d.]+)$",
    "estimated_time": r"^; estimated printing time \(normal mode\) = (.+)$",
    "supports_enabled": r"^; enable_support = (\d+)$",
    "nozzle_diameter_mm": r"^; nozzle_diameter = ([\d.]+)$",
    "print_settings_id": r"^; print_settings_id = (.+)$",
}


def _resolve_slicer(profile: dict[str, Any]) -> tuple[Path, list[Path]] | None:
    config = profile.get("slicer", {})
    program_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None

    executable = program_files / config.get("executable_relative", "ElegooSlicer/elegoo-slicer.exe")
    preset_root = Path(appdata) / "ElegooSlicer" / "system" / "Elegoo"
    preset_keys = ("machine_preset_relative", "process_preset_relative", "filament_preset_relative")
    presets = [preset_root / config[key] for key in preset_keys if config.get(key)]
    if not executable.exists() or len(presets) != 3 or not all(path.exists() for path in presets):
        return None
    return executable, presets


def _parse_gcode(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    metrics: dict[str, Any] = {}
    for key, pattern in METRIC_PATTERNS.items():
        match = re.search(pattern, text, flags=re.MULTILINE)
        if not match:
            continue
        value: Any = match.group(1)
        if key in {"layer_count", "supports_enabled"}:
            value = int(value)
        elif key in {"max_height_mm", "filament_length_mm", "filament_volume_cm3", "nozzle_diameter_mm"}:
            value = float(value)
        metrics[key] = value
    if "supports_enabled" in metrics:
        metrics["supports_enabled"] = bool(metrics["supports_enabled"])
    return metrics


def slice_stl(stl_path: Path, output_dir: Path, profile: dict[str, Any]) -> dict[str, Any]:
    resolved = _resolve_slicer(profile)
    if resolved is None:
        return {"status": "not_run", "reason": "ElegooSlicer executable or declared presets not found"}

    executable, presets = resolved
    output_dir.mkdir(parents=True, exist_ok=True)
    for old_gcode in output_dir.glob("*.gcode"):
        old_gcode.unlink()

    command = [
        str(executable),
        "--arrange", "1",
        "--orient", "0",
        "--load-settings", f"{presets[0]};{presets[1]}",
        "--load-filaments", str(presets[2]),
        "--slice", "0",
        "--outputdir", str(output_dir),
        str(stl_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    gcode_files = list(output_dir.glob("*.gcode"))
    if completed.returncode != 0 or len(gcode_files) != 1:
        return {
            "status": "fail",
            "return_code": completed.returncode,
            "reason": "Slicer did not produce exactly one G-code file",
            "log_tail": (completed.stdout + completed.stderr)[-2000:],
        }

    metrics = _parse_gcode(gcode_files[0])
    expected_supports = bool(profile["process"].get("supports_enabled", False))
    metrics_ok = metrics.get("layer_count", 0) > 0 and metrics.get("max_height_mm", 0) > 0
    supports_ok = metrics.get("supports_enabled") == expected_supports
    return {
        "status": "pass" if metrics_ok and supports_ok else "fail",
        "gcode": str(gcode_files[0]),
        "metrics": metrics,
        "checks": {
            "positive_layers_and_height": metrics_ok,
            "supports_match_profile": supports_ok,
        },
    }
