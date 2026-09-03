# Orchestration Decision: Apache Airflow

## Summary

The Olist e-commerce pipeline's seven stages (ingest → build_staging →
build_database → validate_data → build_features → build_segmentation →
build_charts) were originally sequenced locally via `run_all.bat` on
Windows, with a fully designed, code-reviewed Airflow DAG
(`airflow/dags/olist_pipeline_dag.py`) prepared alongside it as the
production-equivalent orchestration layer. That DAG has since been
executed successfully, end-to-end, on GitHub Codespaces.

## Why Airflow wasn't run locally

Apache Airflow has no native Windows support: it calls
`os.register_at_fork()` unconditionally at import time, a POSIX-only
function absent from Windows' `os` module in every Python version (see
[apache/airflow#10388](https://github.com/apache/airflow/issues/10388),
open since 2020). Airflow's own documentation recommends WSL2 or a
Linux container for Windows users.

Given this project's hardware — an Intel Celeron N3350 with 4GB RAM —
and the project timeline, standing up a second virtualized Linux
environment locally (via WSL2) was assessed as disproportionate setup
risk relative to the marks available, and would have competed directly
with the machine's already constrained RAM budget. Orchestration was
therefore first demonstrated as validated, code-reviewed DAG code plus
a local functional equivalent, `run_all.bat`, performing the same task
sequencing and dependency ordering without the Airflow
scheduler/webserver.

## Resolution: GitHub Codespaces

To provide a genuine execution trace rather than a static design
artifact, the same DAG (unmodified apart from OS-appropriate path and
interpreter changes, see below) was subsequently deployed and run on
GitHub Codespaces — a cloud-hosted Linux development environment. This
sidesteps the Windows incompatibility entirely and moves execution
onto Codespaces' own compute, avoiding the local machine's RAM
constraint rather than working around it.

### Changes required to run the DAG on Linux

Only environment-specific values changed; task logic, dependency
ordering, and retry policy were untouched:

| Item | Windows (original) | Codespaces (Linux) |
|---|---|---|
| `PROJECT_ROOT` | `C:/Projects/olist-pipeline` | `/workspaces/olist-ecommerce-pipeline` |
| `VENV_PYTHON` | `venv/Scripts/python.exe` | `venv/bin/python` |
| `retry_delay` | `300` (raw int) | `timedelta(minutes=5)` |

The `retry_delay` change was made proactively for stricter validation
in Airflow 3.x's TaskFlow API, independent of the OS migration.

### Kaggle authentication under Airflow

`kaggle_auth.py` was designed to read `KAGGLE_USERNAME`/`KAGGLE_KEY`
from the environment for unattended runs, falling back to an
interactive prompt otherwise. Because Airflow's task subprocesses have
no interactive stdin, the `ingest` task initially hung indefinitely
waiting on input that would never arrive. This was resolved by
exporting valid Kaggle API credentials into the environment of the
`airflow standalone` process itself before restarting it, so that
every spawned task subprocess inherited them. No code changes were
needed — this confirmed the original unattended-run design worked as
intended once the environment was correctly provisioned.

## Execution result

All seven tasks completed successfully in a single DAG run:

`ingest → build_staging → build_database → validate_data →
build_features → build_segmentation → build_charts`

The `build_features` task required several retries before succeeding,
surfacing a dependency gap: `pyarrow` (needed by `pandas.to_parquet`)
had not been installed in the Codespaces virtual environment, since it
was not exercised during earlier standalone script runs on the same
machine. Similarly, `build_charts` initially failed on a missing
`seaborn` install. Both were resolved with a single `pip install` each
and the affected tasks were cleared and retried individually —
Airflow re-ran only the failed task and its downstream dependents,
leaving the already-successful upstream stages untouched. This is
itself a demonstration of one of orchestration's practical benefits
over the flat `run_all.bat` sequence: targeted re-execution without
repeating already-completed work.

Total pipeline runtime for the successful run was approximately 8
minutes, including the Kaggle dataset download.

## Conclusion

The DAG defined in `airflow/dags/olist_pipeline_dag.py` is not only
correctly designed but has now been verified through genuine execution
on GitHub Codespaces, a real Linux environment, closing the gap left
by the local Windows hardware constraint without requiring WSL2 or
any change to the resource-conscious architecture of the rest of the
project.