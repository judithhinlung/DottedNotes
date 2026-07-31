#!/usr/bin/env python3
"""Count `/api/convert` requests logged by the deployed web service.

Wraps the Render CLI (`render logs`) to query the "conversion request: ..."
INFO line web.py logs per /api/convert call, and counts how many showed up
in a given time window. Requires the Render CLI to be installed and logged
in (`render login`) -- see the render-logs skill/README for that setup.

Usage:
    scripts/count_conversion_requests.py [--since ISO8601] [--until ISO8601]
        [--resource SERVICE_ID] [--limit N] [--verbose]

Examples:
    scripts/count_conversion_requests.py
    scripts/count_conversion_requests.py --since 2026-07-01T00:00:00Z
    scripts/count_conversion_requests.py --since 2026-07-01 --verbose
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone

DEFAULT_RESOURCE_ID = "srv-d9cntge1a83c739fgoig"  # dottednotes web service
LOG_TEXT_FILTER = "conversion request"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--since",
        default=None,
        help="Start of the query window (ISO8601). Defaults to 30 days ago.",
    )
    parser.add_argument(
        "--until",
        default=None,
        help="End of the query window (ISO8601). Defaults to now.",
    )
    parser.add_argument(
        "--resource",
        default=DEFAULT_RESOURCE_ID,
        help=f"Render service ID to query (default: {DEFAULT_RESOURCE_ID}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Max log entries Render should return (default: 1000).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each matching log entry's timestamp and job_id, not just the total.",
    )
    return parser.parse_args()


def iter_json_objects(raw: str):
    """`render logs --output json` prints concatenated JSON objects (not an
    array or JSON-lines), so a plain json.loads()/one-object-per-line parse
    doesn't work -- decode them one at a time instead."""
    decoder = json.JSONDecoder()
    idx = 0
    raw = raw.strip()
    while idx < len(raw):
        while idx < len(raw) and raw[idx].isspace():
            idx += 1
        if idx >= len(raw):
            break
        obj, end = decoder.raw_decode(raw, idx)
        yield obj
        idx = end


def main() -> int:
    args = parse_args()

    if shutil.which("render") is None:
        print("Error: 'render' CLI not found on PATH. Install it and run 'render login' first.", file=sys.stderr)
        return 1

    since = args.since or (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    cmd = [
        "render", "logs",
        "-r", args.resource,
        "--text", LOG_TEXT_FILTER,
        "--start", since,
        "--limit", str(args.limit),
        "--output", "json",
    ]
    if args.until:
        cmd += ["--end", args.until]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running render logs:\n{result.stderr}", file=sys.stderr)
        return 1

    entries = list(iter_json_objects(result.stdout))
    entries.sort(key=lambda e: e.get("timestamp", ""))

    if args.verbose:
        for entry in entries:
            print(f"{entry.get('timestamp')} - {entry.get('message')}")

    print(f"{len(entries)} conversion request(s) found since {since}"
          + (f" until {args.until}" if args.until else ""))

    if len(entries) >= args.limit:
        print(
            f"Note: result count equals --limit ({args.limit}) -- there may be more; "
            "narrow the time window or raise --limit.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
