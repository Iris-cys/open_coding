# Public release provenance

The complete installable package is published in `Iris-cys/open_coding/local-spec-search`.

The two project commits were replayed into this repository (original local IDs 935c87f and f76c061). Commit hashes change because the destination parent and directory layout differ. Unrelated private-repository history was not copied.

The public-release commit updates repository URLs and installs a repository-root CI workflow. CI tests Python 3.11/3.12 on Linux, Windows and macOS, including wheel reinstallation and direct Git URL installation.

`VALIDATION.md` and `results/` retain historical PCIe 7.0 evaluation results from the predecessor v2 retriever. The frozen first-run set is at `../benchmarks/frozen_holdout_first_run.json`. Historical source fingerprints describe that predecessor, not this repackaged source tree. PDF source files and SQLite indexes are not distributed.

Cloud model clients may send retrieved source text off the machine; use an approved local model for confidential documents.
