# Changelog

All notable changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.0] - 2026-11-09

### Added
- Milestone 2: data models and metric layer. A dbt project on DuckDB with a BigQuery
  target: sources with freshness checks, UTC staging, seeds from the catalog, case
  lifecycle and tier periods, a star schema with a type 2 customer dimension, an
  enforced contract on `fct_cases`, an incremental event fact, additive daily metric
  components and a daily backlog, and reconciliation tests.
- `metrics/metrics.yml` with 11 governed metrics, `support-bi metric` and
  `support-bi metrics`, and the metric dictionary.
- Architecture notes and four design decision records.

## [0.1.0] - 2026-11-02

### Added
- Milestone 1: case data. Reference catalog of products, priorities with first-response
  targets, customer tiers and regions; a seeded generator for customers with tier
  history, agents, cases, case lifecycle events and satisfaction surveys; a Parquet raw
  zone with a checksummed manifest; the `support-bi generate` and `support-bi verify`
  commands.
- Project foundation: package layout, CI (ruff, mypy in strict mode, pytest on Python
  3.11 to 3.13), roadmap, issue and pull request templates.

[Unreleased]: https://github.com/mohammadazam7/cloud-support-bi/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/mohammadazam7/cloud-support-bi/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/mohammadazam7/cloud-support-bi/releases/tag/v0.1.0
