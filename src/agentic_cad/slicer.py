from __future__ import annotations

import json
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
    "first_layer_bed_temperature_c": r"^; first_layer_bed_temperature = ([\d.]+)$",
    "first_layer_nozzle_temperature_c": r"^; first_layer_temperature = ([\d.]+)$",
    "brim_width_mm": r"^; brim_width = ([\d.]+)$",
    "brim_type": r"^; brim_type = (.+)$",
    "bed_type": r"^; curr_bed_type = (.+)$",
}

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_slicer(
    profile: dict[str, Any],
    process_preset_project_relative: str | None = None,
) -> tuple[Path, list[Path]] | None:
    config = profile.get("slicer", {})
    program_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None

    executable = program_files / config.get("executable_relative", "ElegooSlicer/elegoo-slicer.exe")
    preset_root = Path(appdata) / "ElegooSlicer" / "system" / "Elegoo"
    machine = preset_root / config["machine_preset_relative"]
    process = (
        PROJECT_ROOT / process_preset_project_relative
        if process_preset_project_relative
        else preset_root / config["process_preset_relative"]
    )
    filament = (
        PROJECT_ROOT / config["filament_preset_project_relative"]
        if config.get("filament_preset_project_relative")
        else preset_root / config["filament_preset_relative"]
    )
    presets = [machine, process, filament]
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
        elif key in {
            "max_height_mm",
            "filament_length_mm",
            "filament_volume_cm3",
            "nozzle_diameter_mm",
            "first_layer_bed_temperature_c",
            "first_layer_nozzle_temperature_c",
            "brim_width_mm",
        }:
            value = float(value)
        metrics[key] = value
    if "supports_enabled" in metrics:
        metrics["supports_enabled"] = bool(metrics["supports_enabled"])
    return metrics


def slice_stl(
    stl_path: Path,
    output_dir: Path,
    profile: dict[str, Any],
    process_preset_project_relative: str | None = None,
) -> dict[str, Any]:
    resolved = _resolve_slicer(profile, process_preset_project_relative)
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
    expected_nozzle = float(profile["material"]["nozzle_temperature_c"])
    expected_bed = float(profile["material"]["bed_temperature_c"])
    expected_brim = 0.0
    if process_preset_project_relative:
        process_config = json.loads((PROJECT_ROOT / process_preset_project_relative).read_text(encoding="utf-8"))
        expected_brim = float(process_config.get("brim_width", 0))
    metrics_ok = metrics.get("layer_count", 0) > 0 and metrics.get("max_height_mm", 0) > 0
    supports_ok = metrics.get("supports_enabled") == expected_supports
    nozzle_ok = metrics.get("first_layer_nozzle_temperature_c") == expected_nozzle
    bed_ok = metrics.get("first_layer_bed_temperature_c") == expected_bed
    brim_ok = metrics.get("brim_width_mm", 0.0) >= expected_brim
    all_ok = metrics_ok and supports_ok and nozzle_ok and bed_ok and brim_ok
    return {
        "status": "pass" if all_ok else "fail",
        "gcode": str(gcode_files[0]),
        "metrics": metrics,
        "checks": {
            "positive_layers_and_height": metrics_ok,
            "supports_match_profile": supports_ok,
            "nozzle_temperature_matches_profile": nozzle_ok,
            "bed_temperature_matches_profile": bed_ok,
            "minimum_brim_width_matches_process": brim_ok,
        },
    }
