# Component Sourcing

## Search Order

1. Query the local catalog by the semantic interface, such as `cantilever-snap`, `dovetail`, `hinge`, `thread`, or `bearing`.
2. Search the catalog by broader mechanism and function terms.
3. Search official upstream repositories and documentation for parametric source.
4. Search mesh communities only for reference or when no editable mechanism exists.
5. Generate a new mechanism only after recording why existing candidates do not fit.

Example commands:

```powershell
agentic-cad-components "snap fit" --engine openscad
agentic-cad-components --interface dovetail
agentic-cad-components bearing --engine build123d --json
```

## Candidate Ranking

Rank evidence in this order:

1. `physically_validated`: printed successfully with a named printer, material, orientation, and profile.
2. `automatically_validated`: passes geometry, motion, mesh, and slicer checks but lacks a physical result.
3. `available_local`: source is present and inspectable but not fully validated.
4. `indexed_remote`: promising upstream source; fetch selectively and validate before trusting it.

Prefer parametric source, paired mating geometry, documented interfaces, and editable B-rep output. A popular STL is evidence that a shape exists, not that it fits this printer or assembly.

## Catalog Entry

Record:

- Stable ID, name, short functional description, and status.
- Engines, categories, semantic interfaces, and capabilities.
- Upstream URL, exact local path when present, version, license, and attribution.
- Automated and physical evidence, including printer profile and measured values.

License is non-blocking metadata for private experiments, but it must remain attached. Preserve notices and re-check terms before publishing, distributing, or using a component commercially.

## Promotion Gate

Before promoting a candidate:

- Confirm parameters generate valid solids and paired bodies remain separate.
- Check the full assembly motion envelope, not only the final pose.
- Pass B-rep, mesh, printability, and slicer checks.
- Print a minimal coupon in the intended orientation and material.
- Record observed fit, damage, insertion force qualitatively, and measured clearances.
- Promote the reusable mechanism or adapter, not the disposable experiment around it.
