"""Command-line entry point: ``support-bi``."""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from support_bi import metrics as metric_layer
from support_bi.generator import GeneratorConfig, generate
from support_bi.raw_zone import verify_raw_zone, write_raw_zone
from support_bi.seeds import write_seeds


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="support-bi", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="generate the synthetic support data into a raw zone")
    g.add_argument("--out", type=Path, default=Path("data/raw"), help="raw zone directory")
    g.add_argument("--seed", type=int, default=GeneratorConfig.seed)
    g.add_argument("--start", type=dt.date.fromisoformat, default=GeneratorConfig.start)
    g.add_argument("--days", type=int, default=GeneratorConfig.days)
    g.add_argument("--customers", type=int, default=GeneratorConfig.customers)
    g.add_argument("--agents", type=int, default=GeneratorConfig.agents)
    g.add_argument("--cases-per-day", type=float, default=GeneratorConfig.cases_per_day)

    v = sub.add_parser("verify", help="check raw zone files against their manifest")
    v.add_argument("--out", type=Path, default=Path("data/raw"), help="raw zone directory")

    s = sub.add_parser("seeds", help="write the catalog as dbt seed files")
    s.add_argument("--out", type=Path, default=Path("dbt/seeds"), help="seed directory")

    m = sub.add_parser("metrics", help="write the metric dictionary from metrics/metrics.yml")
    m.add_argument("--out", type=Path, default=Path("docs/metric_dictionary.md"))

    q = sub.add_parser("metric", help="print the SQL for one metric, or run it on DuckDB")
    q.add_argument("name", help="metric name from metrics/metrics.yml")
    q.add_argument("--by", action="append", default=[], help="dimension to group by")
    q.add_argument("--where", action="append", default=[], metavar="DIM=VALUE")
    q.add_argument("--warehouse", type=Path, help="DuckDB file to run the query against")
    return p


def _metric(args: argparse.Namespace) -> int:
    defined = metric_layer.load()
    if args.name not in defined:
        print(f"unknown metric {args.name}; known: {', '.join(defined)}", file=sys.stderr)
        return 2
    where = dict(item.split("=", 1) for item in args.where)
    query = metric_layer.sql(defined[args.name], group_by=args.by, where=where)
    if args.warehouse is None:
        print(query)
        return 0
    import duckdb

    with duckdb.connect(str(args.warehouse), read_only=True) as con:
        result = con.execute(query)
        names = [d[0] for d in result.description]
        print("\t".join(names))
        for row in result.fetchall():
            print("\t".join("" if v is None else str(v) for v in row))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if args.command == "generate":
        cfg = GeneratorConfig(
            seed=args.seed,
            start=args.start,
            days=args.days,
            customers=args.customers,
            agents=args.agents,
            cases_per_day=args.cases_per_day,
        )
        manifest = write_raw_zone(generate(cfg), args.out, cfg)
        for name, meta in manifest["tables"].items():
            print(f"{name:<22} {meta['rows']:>9,} rows")
        return 0
    if args.command == "metrics":
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(metric_layer.dictionary(metric_layer.load()), encoding="utf-8")
        print(args.out)
        return 0
    if args.command == "metric":
        return _metric(args)
    if args.command == "seeds":
        for path in write_seeds(args.out):
            print(path)
        return 0
    problems = verify_raw_zone(args.out)
    for p in problems:
        print(p, file=sys.stderr)
    print("raw zone consistent" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
