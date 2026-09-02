# Orchestration: Design Decision and Local Substitute

## What was built

A complete Airflow 3.x DAG (`airflow/dags/olist_pipeline_dag.py`) was
designed and code-reviewed against Airflow's current Task SDK API
(`airflow.sdk.dag`, `airflow.sdk.task`). It orchestrates all seven
pipeline stages as a linear dependency chain:

```
ingest -> build_staging -> build_database -> validate_data
       -> build_features -> build_segmentation -> build_charts
```

Each task invokes the corresponding pipeline script via `subprocess`,
calling the project's main virtual environment interpreter directly
rather than importing pipeline dependencies into Airflow's own
environment. This was a deliberate resource decision: Airflow's own
dependency tree is large, and keeping it isolated from
pandas/scikit-learn/Great Expectations avoids two independently-solved
dependency trees conflicting, and keeps Airflow's own memory footprint
smaller.

The DAG configuration includes a daily schedule, two retries with a
5-minute delay (to absorb transient failures such as a Kaggle API
timeout), and tagging for discoverability in the Airflow UI.

## Why it was not executed

Apache Airflow does not run natively on Windows. Its own codebase calls
`os.register_at_fork()` unconditionally during import
(`airflow/_shared/observability/metrics/stats.py`), and this function
is POSIX-only — it does not exist in Windows' `os` module in any Python
version. This is a long-standing, documented limitation, not a
version- or configuration-specific bug: see
[apache/airflow#10388](https://github.com/apache/airflow/issues/10388),
open since 2020, and Airflow's own installation documentation, which
states that Windows users require WSL2 or Linux containers.

WSL2 was evaluated as the standard remedy. It was not pursued for this
submission because:

1. **Hardware constraints.** The development machine has 4GB of RAM
   (3.83GB usable) on an Intel Celeron N3350. WSL2's Linux VM requires
   a dedicated memory allocation on top of Windows' own usage; even a
   conservative 1.5GB cap leaves very little headroom for running
   VSCode, the pipeline's main environment, and the Linux-side Airflow
   installation simultaneously.
2. **Time-to-value.** Every other tool in this project (Great
   Expectations, DVC, scikit-learn, the SQLite pipeline itself) runs
   natively and reliably on Windows. Introducing a second, virtualized
   operating system solely for one tool represented a
   disproportionate amount of new setup surface, and therefore new
   failure surface, relative to the marks available for this
   component specifically.
3. **The DAG design itself is independently verifiable.** The
   orchestration logic, dependency ordering, retry policy, and
   task-isolation strategy can all be assessed by reading the DAG
   code, independent of whether it was executed in this environment.

## Local substitute: `run_all.bat`

To ensure the pipeline itself remains fully reproducible and runnable
end-to-end without Airflow, `run_all.bat` performs the same task
sequencing and dependency ordering as the DAG, using Windows batch
control flow (`if errorlevel 1 goto :error`) in place of Airflow's task
failure handling. It does not provide scheduling, retries, or a web
UI — this is an explicit, acknowledged reduction in functionality
relative to the designed DAG, not a claim of equivalence.

## Simulated Graph View

`docs/dag_graph_view_simulated.png` shows the DAG's intended structure
as it would appear in Airflow's Graph View after a successful run.
This is a simulation, generated separately from the actual pipeline
outputs, and is labeled as such — it does not represent an actual
Airflow execution.
