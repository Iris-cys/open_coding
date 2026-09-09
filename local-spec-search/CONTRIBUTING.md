# Contributing

Use Python 3.10 or newer. Install the development extras with `python -m pip install -e ".[dev]"`.

A retrieval change is accepted only when it includes a reproducible test or benchmark showing what improved and what regressed. Do not tune against a holdout set and continue calling it blind evaluation. Do not hard-code answer page numbers. Preserve exact source page text and document fingerprints in evaluation outputs.

Before opening a pull request, run:

```bash
python -m unittest discover -s tests -p "test_*.py"
ruff check src tests
python -m build
twine check dist/*
```

Large PDFs, SQLite indexes, proprietary specifications, and benchmark outputs containing copyrighted source text must not be committed.
