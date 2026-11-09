# Roadmap

Each milestone lands on its own branch with tests and is merged when complete. Checked
items are done.

- [x] **M1: Foundation and case data** (Nov 1 to Nov 2). Package layout, CI, a seeded
      generator for customers, agents, cases, case events, CSAT surveys and staffing,
      with realistic seasonality, priority mix and SLA behaviour, written to a raw zone
      as Parquet.
- [x] **M2: Data models and metric layer** (Nov 3 to Nov 7). dbt project on DuckDB and
      BigQuery targets: staging, intermediate and mart layers; star schema with a type 2
      customer dimension; incremental event fact; partitioning and clustering; tests,
      contracts and source freshness; governed metric definitions and a metric
      dictionary.
- [ ] **M3: Dashboards and reporting** (Nov 8 to Nov 10). LookML views, explores and
      dashboards validated in CI, row-level access filters and PII masking, and a weekly
      leadership report built automatically by a scheduled workflow.
- [ ] **M4: Analytics** (Nov 11 to Nov 19). Case volume forecasting with backtests,
      escalation risk model with calibration and feature attributions, SLA breach
      anomaly detection, and an impact analysis of a process change.
- [ ] **M5: Ask the data and Support Command Center** (Nov 20 to Nov 28). Natural
      language questions answered with SQL restricted to the governed metrics, and an
      interactive 3D web app for the support operation.
- [ ] **M6: v1.0** (Nov 29 to Dec 4). Requirements document, multi-quarter roadmap,
      executive readout with recommendations, architecture notes and release.
