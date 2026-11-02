"""Command-line entry point: ``support-bi``."""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from support_bi.generator import GeneratorConfig, generate
from support_bi.raw_zone import verify_raw_zone, write_raw_zone


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
    return p


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
    problems = verify_raw_zone(args.out)
    for p in problems:
        print(p, file=sys.stderr)
    print("raw zone consistent" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
