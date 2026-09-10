# Development environment

Run the VS Code tasks through **Terminal → Run Task**:

- **Env: Snapshot** records exact Linux conda package URLs/builds in
  `conda-linux-64.lock` and ordinary pip packages in `pip-requirements.txt`.
  It excludes editable projects. Direct-URL/local non-editable pip installs are
  rejected rather than silently converted into inaccurate version pins.
- **Env: Sync from lock** checks the conda inventory first. If it differs,
  sync stops without changes and asks you to rebuild. Otherwise, it installs
  missing/different pinned pip packages and removes extra non-editable pip
  packages. Existing editable registrations are preserved. Pip requirements
  cannot replace an editable or conda-owned package.
- **Env: Rebuild from lock** requires typing `rebuild`. It downloads the conda
  packages before removing and recreating `labscript_test_v1`, then installs
  the pip requirements. Close applications using this environment first.
  Editable registrations are removed, but source checkouts remain intact.
  Reinstall your chosen editable projects manually afterward.

The target is `~/.local/share/mamba/envs/labscript_test_v1`. Tasks use system
Python to orchestrate micromamba, so rebuilding does not delete the interpreter
running the task. Network access is needed for uncached packages. A rebuild
is not transactional: failure after removal can leave an incomplete environment;
rerun the rebuild to recover.

Pip installation uses `--no-deps`: dependencies must be captured separately in
the conda lock or pip requirements. Pip versions are pinned, but package artifacts
are not hash-locked. These files describe dependencies, not Git source revisions.
Pulling ordinary Python source changes does not require reinstalling editable
projects; metadata/entry-point changes or compiled extensions can require it.

Sync/rebuild verify both dependency inventories and then run `pip check`.
Metadata issues are advisory and do not fail a successful sync/rebuild. Actual
installation errors or inventory mismatches still produce a nonzero exit. The initial
snapshot has existing missing requirements reported for `labscript-devices`
(`pydaqmx`, `pynivision`, `pyserial`, `pyvisa`, `spinapi`) and `setuptools-conda`
(`ripgrep`, although the conda executable package is installed).

For a manual editable install after restoring dependencies:

```bash
~/.local/share/mamba/envs/labscript_test_v1/bin/python -m pip install --no-deps -e .
```
