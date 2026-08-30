# Testing

This repository keeps the test suite dependency-free. Tests use Python's
standard `unittest` runner so contributors can run them immediately after
`uv sync`.

## Run all tests

```bash
uv run python -m unittest discover -s tests
```

If you are not using `uv`, install the package in an environment with Python
3.11+ and run the same module command:

```bash
python -m unittest discover -s tests
```

## Coverage focus

The current tests cover the parts most likely to break paper builds:

- `manuscript-md` CLI command dispatch and `sync-assets` copy behavior.
- Markdown `@import` expansion, nested import resolution, circular import
  detection, and table indentation normalization.
- Manuscript word counts for abstract, main text sections, citations, figures,
  tables, links, and front matter.
- BibTeX metadata extraction used by reference ingest notes.

## Adding tests

- Place new tests in `tests/test_*.py`.
- Prefer temporary directories for filesystem behavior so tests never require a
  local paper project.
- Keep tests independent of pandoc, Microsoft Word, and a real Paperpile export
  unless the test is explicitly documenting integration behavior.
- When a script lives under a skill folder, prefer importing the matching
  `manuscript_md` module in tests. Skill scripts are thin entry points that call
  into `src/manuscript_md/`.
