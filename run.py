#!/usr/bin/env python3
"""CLI: python run.py --channel motivation [--dry-run] [--upload private|public|unlisted|none]"""

from __future__ import annotations

import argparse
import json

from pipeline.config import list_channels
from pipeline.pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ek roz ek short — trend se video tak, ek hi command me."
    )
    parser.add_argument(
        "--channel",
        default="motivation",
        help=f"channel profile id (channels/*.json). Available: {', '.join(list_channels()) or 'none'}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="sirf idea + script + upload package banao, video render mat karo",
    )
    parser.add_argument(
        "--upload",
        default=None,
        choices=["private", "public", "unlisted", "none"],
        help="upload privacy; default channel profile se aata hai",
    )
    parser.add_argument(
        "--idea",
        default=None,
        help="apna topic force karo (trend/seed ideas ignore honge)",
    )
    parser.add_argument(
        "--shortlist",
        type=int,
        default=3,
        help="kitne idea candidates report me dikhane hain (default 3)",
    )
    args = parser.parse_args()

    summary = run(
        args.channel,
        dry_run=args.dry_run,
        upload_mode=args.upload,
        idea_text=args.idea,
        shortlist=args.shortlist,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
