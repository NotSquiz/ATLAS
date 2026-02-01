"""
Baby Brains CLI

Command-line interface for Baby Brains automation.

Usage:
    python -m atlas.babybrains.cli status
    python -m atlas.babybrains.cli find-doc <topic>
    python -m atlas.babybrains.cli warming daily [--platform youtube]
    python -m atlas.babybrains.cli warming done <platform> <actions>
    python -m atlas.babybrains.cli warming status
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from atlas.babybrains import db
from atlas.babybrains.cross_repo import get_cross_repo_search

logger = logging.getLogger(__name__)


def get_conn():
    """Get database connection with BB tables initialized."""
    conn = db.get_bb_connection()
    db.init_bb_tables(conn)
    return conn


def cmd_status(args):
    """Show full Baby Brains status dashboard."""
    conn = get_conn()
    status = db.get_bb_status(conn)

    print("\n=== BABY BRAINS STATUS ===\n")

    # Accounts
    print("ACCOUNTS:")
    if status["accounts"]:
        for a in status["accounts"]:
            extra = ""
            if a.get("incubation_end_date"):
                extra = f" (until {a['incubation_end_date']})"
            handle = a['handle'] if a['handle'].startswith('@') else a['handle']
            print(f"  {a['platform']:12s} {handle:20s} [{a['status']}]{extra} {a['followers']} followers")
    else:
        print("  No accounts registered. Use bb_warming_daily to get started.")

    # Today
    print(f"\nTODAY:")
    print(f"  Targets: {status['today']['targets']}")
    print(f"  Pending: {status['today']['pending']}")
    print(f"  Completed: {status['today']['completed']}")

    # 7-day warming stats
    w = status["warming_7d"]
    print(f"\nWARMING (7 days):")
    print(f"  Watches: {w['watches']}  Likes: {w['likes']}  Subscribes: {w['subscribes']}  Comments: {w['comments']}")
    print(f"  Total watch time: {w['total_watch_minutes']} min")

    # Trends
    print(f"\nTRENDS:")
    print(f"  Recent: {status['trends']['recent_count']}")
    if status["trends"]["top_topics"]:
        for t in status["trends"]["top_topics"]:
            print(f"    - {t}")

    # Content
    print(f"\nCONTENT:")
    print(f"  Draft briefs: {status['content']['draft_briefs']}")

    print()
    conn.close()


def cmd_accounts_populate(args):
    """Populate bb_accounts with the 4 Baby Brains social accounts."""
    conn = get_conn()
    results = db.populate_accounts(conn)

    print("\n=== ACCOUNTS POPULATE ===\n")
    for r in results:
        print(f"  {r['platform']:12s} {r['handle']:20s} [{r['status']}] {r['action']}")

    print(f"\n{len(results)} accounts processed.")
    conn.close()


def cmd_find_doc(args):
    """Search across all BB repos for relevant documents."""
    search = get_cross_repo_search()
    results = search.search(args.topic, limit=args.limit)

    if not results:
        print(f"No documents found for: {args.topic}")
        return

    print(f"\n=== Documents matching '{args.topic}' ===\n")
    for r in results:
        exists_marker = "+" if r["exists"] else "-"
        print(f"  [{exists_marker}] {r['repo']}/{r['path']}")
        print(f"      {r['summary']}")
        print(f"      Topic: {r['topic']} | Score: {r['score']}")
        print()


def cmd_warming_daily(args):
    """Show today's warming targets with comments."""
    conn = get_conn()
    platform = args.platform

    targets = db.get_warming_targets(conn, platform=platform)

    if not targets:
        print(f"\nNo warming targets for today{f' ({platform})' if platform else ''}.")
        print("Run bb_morning_prep or add targets manually.")
        conn.close()
        return

    print(f"\n=== WARMING TARGETS{f' ({platform})' if platform else ''} ===\n")
    for i, t in enumerate(targets, 1):
        status_marker = {"pending": "[ ]", "completed": "[x]", "skipped": "[-]"}.get(t.status, "[?]")
        print(f"{status_marker} {i}. [{t.engagement_level}] {t.video_title or t.url}")
        print(f"   Channel: {t.channel_name or 'Unknown'}")
        print(f"   Watch: {t.watch_duration_target}s | Relevance: {t.niche_relevance_score:.1f}")
        if t.transcript_summary:
            print(f"   Summary: {t.transcript_summary[:120]}...")
        if t.suggested_comment:
            print(f"   Comment: {t.suggested_comment}")
        print()

    conn.close()


def cmd_warming_done(args):
    """Log completed warming actions."""
    conn = get_conn()

    # Parse actions like "3 comments, 2 likes, 1 subscribe"
    actions_text = " ".join(args.actions)
    print(f"Logging warming actions for {args.platform}: {actions_text}")

    # Simple parser: look for "N action" patterns
    import re
    patterns = re.findall(r"(\d+)\s*(comment|like|subscribe|watch|follow)", actions_text, re.IGNORECASE)

    for count_str, action_type in patterns:
        count = int(count_str)
        for _ in range(count):
            db.log_warming_action(conn, target_id=0, action_type=action_type.lower())
        print(f"  Logged {count} {action_type}(s)")

    print("Done.")
    conn.close()


def cmd_warming_status(args):
    """Show warming statistics."""
    conn = get_conn()
    stats = db.get_warming_stats(conn, days=args.days)

    print(f"\n=== WARMING STATUS ({stats['period_days']} days) ===\n")
    print(f"  Total targets: {stats['total_targets']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Watches: {stats['watches']}")
    print(f"  Likes: {stats['likes']}")
    print(f"  Subscribes: {stats['subscribes']}")
    print(f"  Comments: {stats['comments']}")
    print(f"  Watch time: {stats['total_watch_minutes']} min")
    print()

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        prog="bb",
        description="Baby Brains Automation CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status
    subparsers.add_parser("status", help="Show BB status dashboard")

    # find-doc
    find_doc = subparsers.add_parser("find-doc", help="Search cross-repo documents")
    find_doc.add_argument("topic", help="Topic to search for")
    find_doc.add_argument("--limit", type=int, default=10, help="Max results")

    # accounts
    accounts = subparsers.add_parser("accounts", help="Account management commands")
    accounts_sub = accounts.add_subparsers(dest="accounts_command")
    accounts_sub.add_parser("populate", help="Populate 4 BB social accounts")

    # warming
    warming = subparsers.add_parser("warming", help="Warming pipeline commands")
    warming_sub = warming.add_subparsers(dest="warming_command")

    # warming daily
    wd = warming_sub.add_parser("daily", help="Show today's targets")
    wd.add_argument("--platform", help="Filter by platform")

    # warming done
    wdone = warming_sub.add_parser("done", help="Log completed actions")
    wdone.add_argument("platform", help="Platform name")
    wdone.add_argument("actions", nargs="+", help="Actions (e.g., '3 comments 2 likes')")

    # warming status
    ws = warming_sub.add_parser("status", help="Show warming stats")
    ws.add_argument("--days", type=int, default=7, help="Days to look back")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "find-doc":
        cmd_find_doc(args)
    elif args.command == "accounts":
        if args.accounts_command == "populate":
            cmd_accounts_populate(args)
        else:
            accounts.print_help()
    elif args.command == "warming":
        if args.warming_command == "daily":
            cmd_warming_daily(args)
        elif args.warming_command == "done":
            cmd_warming_done(args)
        elif args.warming_command == "status":
            cmd_warming_status(args)
        else:
            warming.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
