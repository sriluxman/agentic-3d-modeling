from pathlib import Path

from agentic_cad.catalog import find_catalog, load_catalog, search_components


ROOT = Path(__file__).resolve().parents[1]


def test_physically_validated_snap_fit_ranks_first() -> None:
    catalog = load_catalog(ROOT / "components" / "catalog.json")

    matches = search_components(catalog, "snap fit", engine="openscad")

    assert matches[0]["id"] == "fpetrac-snaplib-0.36"
    assert matches[0]["status"] == "physically_validated"


def test_interface_filter_finds_reusable_dovetails() -> None:
    catalog = load_catalog(ROOT / "components" / "catalog.json")

    matches = search_components(catalog, interface="dovetail")

    assert {match["id"] for match in matches} == {"bosl2", "jointscad"}


def test_unknown_mechanism_has_no_match() -> None:
    catalog = load_catalog(ROOT / "components" / "catalog.json")

    assert search_components(catalog, "nonexistent-mechanism") == []


def test_catalog_is_found_from_nested_working_directory(monkeypatch) -> None:
    monkeypatch.chdir(ROOT / "models" / "python")

    assert find_catalog().resolve() == (ROOT / "components" / "catalog.json").resolve()
