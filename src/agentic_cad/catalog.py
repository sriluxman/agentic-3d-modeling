from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_CATALOG = Path("components/catalog.json")
STATUS_WEIGHT = {
    "physically_validated": 50,
    "automatically_validated": 35,
    "available_local": 20,
    "indexed_remote": 10,
}


def load_catalog(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        catalog = json.load(handle)
    if catalog.get("schema_version") != 1 or not isinstance(catalog.get("components"), list):
        raise ValueError(f"Unsupported component catalog: {path}")
    return catalog


def find_catalog(path: Path = DEFAULT_CATALOG) -> Path:
    if path != DEFAULT_CATALOG or path.exists():
        return path
    for parent in Path.cwd().resolve().parents:
        candidate = parent / path
        if candidate.exists():
            return candidate
    return path


def _terms(value: str) -> set[str]:
    return {term for term in re.split(r"[^a-z0-9]+", value.lower()) if term}


def _values(component: dict[str, Any], key: str) -> list[str]:
    value = component.get(key, [])
    return value if isinstance(value, list) else [str(value)]


def search_components(
    catalog: dict[str, Any],
    query: str = "",
    *,
    engine: str | None = None,
    category: str | None = None,
    interface: str | None = None,
) -> list[dict[str, Any]]:
    query_terms = _terms(query)
    results: list[tuple[int, dict[str, Any]]] = []

    for component in catalog["components"]:
        engines = {value.lower() for value in _values(component, "engines")}
        categories = {value.lower() for value in _values(component, "categories")}
        interfaces = {value.lower() for value in _values(component, "interfaces")}
        if engine and engine.lower() not in engines:
            continue
        if category and category.lower() not in categories:
            continue
        if interface and interface.lower() not in interfaces:
            continue

        searchable = " ".join(
            [
                component.get("id", ""),
                component.get("name", ""),
                component.get("description", ""),
                *engines,
                *categories,
                *interfaces,
                *_values(component, "capabilities"),
            ]
        )
        searchable_terms = _terms(searchable)
        matched = query_terms & searchable_terms
        if query_terms and not query_terms.issubset(searchable_terms):
            continue

        score = STATUS_WEIGHT.get(component.get("status", ""), 0) + len(matched) * 5
        score += len(query_terms & _terms(" ".join(interfaces))) * 4
        score += len(query_terms & _terms(" ".join(categories))) * 2
        result = dict(component)
        result["match_score"] = score
        results.append((score, result))

    return [component for _, component in sorted(results, key=lambda item: (-item[0], item[1]["name"]))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Find reusable parametric CAD components")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--engine")
    parser.add_argument("--category")
    parser.add_argument("--interface")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    matches = search_components(
        load_catalog(find_catalog(args.catalog)),
        args.query,
        engine=args.engine,
        category=args.category,
        interface=args.interface,
    )
    if args.json:
        print(json.dumps(matches, indent=2))
    else:
        for match in matches:
            source = match["source"]
            location = source.get("local_path") or source["url"]
            print(f"{match['id']} [{match['status']}] score={match['match_score']}")
            print(f"  {match['description']}")
            print(f"  {location}")
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
