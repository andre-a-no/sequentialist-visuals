# Repository guidance

This is `sequentialist-visuals`, the reusable **software-engineering** visualization
package. `sequential-*` repositories own mathematical/cybernetic methods;
`sequentialist-*` repositories own engineering and applications. This package
renders supplied records; it must not decide, validate proofs, calibrate scores
or infer statistical guarantees.

## Read first

- [README.md](README.md): installation, input schemas and executable examples.
- [docs/overview.md](docs/overview.md): plain-language use cases, current limits
  and a workflow for people who do not program.
- [llms.txt](llms.txt): a curated reading index; client discovery behavior varies.

## Source map

- [render.py](src/sequentialist/visuals/render.py): `render_search` and
  `render_timeline`, validation, escaping, HTML/SVG generation.
- [__init__.py](src/sequentialist/visuals/__init__.py): public API exports.
- [test_render.py](tests/test_render.py): input isolation, unsafe text, graph
  references, causality, time boundaries and rendering behavior.
- [pyproject.toml](pyproject.toml): Python floor, packaging and check settings.

Use the existing checkout. Preserve unrelated work. Keep HTML standalone and
offline; never interpolate unescaped caller data into markup or introduce hidden
I/O. Keep caller record order and distinguish explicit causes from display
order. Add focused tests when changing these contracts. Do not change package
identity, dependency declarations or public guarantees as an incidental cleanup.

## Checks

Run from the repository root with development tools installed:

```bash
PYTHONPATH=src python -m pytest -q tests
python -m ruff check src tests
python -m mypy
git diff --check
```

These commands were exercised for the current implementation. For prose-only
changes, use `git diff --check`, verify changed relative links and confirm that
examples match the current API. Rerun executable examples when their commands or
payloads change; a full implementation test run is not required for a typo fix.

No publication, push or external message is implied by repository maintenance.
