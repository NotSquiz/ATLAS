"""
Baby Brains CLI

Command-line interface for Baby Brains automation.

Usage:
    python -m atlas.babybrains.cli status
    python -m atlas.babybrains.cli find-doc <topic>
    python -m atlas.babybrains.cli warming daily [--platform youtube]
    python -m atlas.babybrains.cli warming done <platform> <actions>
    python -m atlas.babybrains.cli warming status

    # Trend detection (S2.6-lite)
    python -m atlas.babybrains.cli trends scan [--focus X] [--max 10]
    python -m atlas.babybrains.cli trends latest [--limit 10]
    python -m atlas.babybrains.cli trends budget
    python -m atlas.babybrains.cli trends suggest [-n 5]

    # Content production pipeline (Phase 1.5)
    python -m atlas.babybrains.cli content brief --topic "Tummy time" --age "0-6m"
    python -m atlas.babybrains.cli content qc --script-id 1
    python -m atlas.babybrains.cli content status
    python -m atlas.babybrains.cli content pipeline --brief-id 1
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


def cmd_warming_run(args):
    """Run full daily warming: generate targets + browser session."""
    import asyncio

    logging.basicConfig(level=logging.INFO, format="  %(message)s")

    conn = get_conn()
    platform = args.platform or "youtube"

    print(f"\n=== DAILY WARMING ({platform}) ===\n")

    from atlas.babybrains.warming.service import WarmingService
    service = WarmingService(conn=conn)

    # Step 1: Generate targets
    print("  [1/2] Generating targets from YouTube API...")
    count = asyncio.run(service.morning_prep(platform=platform))
    if count > 0:
        print(f"  Created {count} new targets.\n")
    else:
        # Check if targets already exist
        existing = db.get_warming_targets(conn, platform=platform)
        pending = [t for t in existing if t.status == "pending"]
        if pending:
            print(f"  {len(pending)} targets already queued.\n")
        else:
            print("  No targets available. Check YOUTUBE_API_KEY is set.\n")
            conn.close()
            return

    # Step 2: Run browser session
    print("  [2/2] Starting browser warming session...")
    result = asyncio.run(service.run_browser_session(platform=platform))

    if result.get("status") == "error":
        print(f"\n  ERROR: {result['message']}")
    elif result.get("status") == "no_targets":
        print(f"\n  {result['message']}")
    elif result.get("status") == "aborted":
        print(f"\n  Session ABORTED: {result.get('abort_reason')}")
    else:
        print(f"\n  Done! {result.get('videos_watched', 0)} videos, "
              f"{result.get('total_watch_seconds', 0)}s watched, "
              f"{result.get('likes', 0)} likes, "
              f"{result.get('subscribes', 0)} subscribes")

    print()
    conn.close()


def cmd_warming_prep(args):
    """Generate today's warming targets from YouTube API."""
    import asyncio

    logging.basicConfig(level=logging.INFO, format="  %(message)s")

    conn = get_conn()
    platform = args.platform or "youtube"

    print(f"\n=== MORNING PREP ({platform}) ===\n")

    from atlas.babybrains.warming.service import WarmingService

    service = WarmingService(conn=conn)
    count = asyncio.run(service.morning_prep(platform=platform))

    if count > 0:
        print(f"  Created {count} warming targets for today.")
        print(f"  Run: python -m atlas.babybrains.cli warming watch")
    else:
        print("  No new targets created.")
        print("  (Targets may already exist, or YOUTUBE_API_KEY may not be set)")

    print()
    conn.close()


def cmd_warming_daily(args):
    """Show today's warming targets with comments."""
    conn = get_conn()
    platform = args.platform

    targets = db.get_warming_targets(conn, platform=platform)

    if not targets:
        print(f"\nNo warming targets for today{f' ({platform})' if platform else ''}.")
        print("Run: python -m atlas.babybrains.cli warming prep")
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


def cmd_warming_watch(args):
    """Run an automated browser warming session."""
    import asyncio

    # Enable logging so user can see progress
    logging.basicConfig(
        level=logging.INFO,
        format="  %(message)s",
    )

    conn = get_conn()
    platform = args.platform or "youtube"

    print(f"\n=== STARTING WARMING SESSION ({platform}) ===\n")

    from atlas.babybrains.warming.service import WarmingService

    service = WarmingService(conn=conn)
    result = asyncio.run(service.run_browser_session(platform=platform))

    if result.get("status") == "error":
        print(f"  ERROR: {result['message']}")
    elif result.get("status") == "no_targets":
        print(f"  {result['message']}")
        print("  Add targets with: bb warming daily")
    elif result.get("status") == "aborted":
        print(f"  Session ABORTED: {result.get('abort_reason')}")
        print(f"  Videos watched before abort: {result.get('videos_watched', 0)}")
    else:
        print(f"  Videos watched: {result.get('videos_watched', 0)}")
        print(f"  Watch time: {result.get('total_watch_seconds', 0)}s")
        print(f"  Likes: {result.get('likes', 0)}")
        print(f"  Subscribes: {result.get('subscribes', 0)}")
        print(f"  Actions logged: {result.get('actions_logged', 0)}")

    if result.get("errors"):
        print(f"\n  Errors:")
        for err in result["errors"]:
            print(f"    - {err}")

    print()
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

    # Browser session stats
    browser_stats = db.get_browser_session_stats(conn, days=args.days)
    if (browser_stats["successful_sessions"] > 0
            or browser_stats["failed_sessions"] > 0):
        print(f"\n  BROWSER SESSIONS:")
        print(f"    Successful: {browser_stats['successful_sessions']}")
        print(f"    Failed: {browser_stats['failed_sessions']}")
        print(f"    Session watch time: {browser_stats['total_session_watch_minutes']} min")
        if browser_stats.get("last_session"):
            last = browser_stats["last_session"]
            print(f"    Last session: {last['type']} at {last['at']}")
        if browser_stats.get("last_failure") and browser_stats["last_failure"]["reason"]:
            fail = browser_stats["last_failure"]
            print(f"    Last failure: {fail['reason']}")

    print()
    conn.close()


# ============================================
# CONTENT PRODUCTION COMMANDS
# ============================================


def cmd_content_brief(args):
    """Create a content brief."""
    conn = get_conn()
    db.run_content_migration(conn)

    brief_id = db.add_content_brief(
        conn,
        topic=args.topic,
        age_range=args.age,
        montessori_principle=args.principle,
        target_length=args.length,
        content_pillar=args.pillar,
    )

    print(f"\n=== CONTENT BRIEF CREATED ===\n")
    print(f"  Brief ID: {brief_id}")
    print(f"  Topic: {args.topic}")
    print(f"  Age range: {args.age}")
    print(f"  Target length: {args.length}")
    if args.principle:
        print(f"  Montessori principle: {args.principle}")
    if args.pillar:
        print(f"  Content pillar: {args.pillar}")
    print(f"\n  Next: python -m atlas.babybrains.cli content script --brief-id {brief_id}")
    print()
    conn.close()


def cmd_content_script(args):
    """Generate a script for a brief (placeholder - requires skill execution)."""
    conn = get_conn()
    db.run_content_migration(conn)

    brief = db.get_brief_by_id(conn, args.brief_id)
    if not brief:
        print(f"Error: Brief {args.brief_id} not found")
        conn.close()
        return

    print(f"\n=== SCRIPT GENERATION ===\n")
    print(f"  Brief ID: {args.brief_id}")
    print(f"  Topic: {brief.topic}")
    print(f"  Template: {args.template}")
    print()
    print("  NOTE: Script generation requires the bb_script_write skill.")
    print("  This command is a placeholder - use the full pipeline for generation.")
    print(f"\n  Run: python -m atlas.babybrains.cli content pipeline --brief-id {args.brief_id}")
    print()
    conn.close()


def cmd_content_localise(args):
    """Add AU localisation cues to a script (placeholder)."""
    print(f"\n=== AU LOCALISATION ===\n")
    print(f"  Script ID: {args.script_id}")
    print()
    print("  NOTE: Localisation requires the bb_au_localise skill.")
    print("  This command is a placeholder - use the full pipeline.")
    print()


def cmd_content_prompts(args):
    """Generate visual prompts for a script (placeholder)."""
    print(f"\n=== PROMPT GENERATION ===\n")
    print(f"  Script ID: {args.script_id}")
    print(f"  Tool: {args.tool}")
    print()
    print("  NOTE: Prompt generation requires the bb_prompt_generate skill.")
    print("  This command is a placeholder - use the full pipeline.")
    print()


def cmd_content_qc(args):
    """Run QC hooks on a script."""
    import asyncio
    from atlas.orchestrator.hooks import HookRunner, HookTiming

    conn = get_conn()
    db.run_content_migration(conn)

    script = db.get_script_by_id(conn, args.script_id)
    if not script:
        print(f"Error: Script {args.script_id} not found")
        conn.close()
        return

    brief = db.get_brief_by_id(conn, script.brief_id) if script.brief_id else None

    print(f"\n=== SCRIPT QC ===\n")
    print(f"  Script ID: {args.script_id}")
    print(f"  Format: {script.format_type}")
    print(f"  Word count: {script.word_count}")
    print()

    runner = HookRunner()

    # Build input for stdin-based hooks
    qc_input = {
        "scenes": script.scenes,
        "format_type": script.format_type,
        "total_word_count": script.word_count,
    }

    # Run qc_script hook
    result = asyncio.run(runner.run(
        "babybrains_content",
        "qc_script",
        input_data=qc_input,
    ))

    if result.passed:
        print("  [PASS] qc_script")
    else:
        print("  [FAIL] qc_script")
        for issue in result.issues:
            severity = "X" if issue.severity == "block" else "!"
            print(f"    {severity} [{issue.code}] {issue.message}")

    print()
    conn.close()


def cmd_content_qc_audio(args):
    """Run audio QC hook on a file."""
    import asyncio
    from atlas.orchestrator.hooks import HookRunner

    print(f"\n=== AUDIO QC ===\n")
    print(f"  File: {args.file}")
    print(f"  Master: {args.master}")
    print()

    runner = HookRunner()
    cli_args = [args.file]
    if args.master:
        cli_args.append("--master")

    result = asyncio.run(runner.run(
        "babybrains_content",
        "qc_audio",
        cli_args=cli_args,
    ))

    if result.passed:
        print("  [PASS] Audio levels within spec")
    else:
        print("  [FAIL] Audio QC failed")
        for issue in result.issues:
            severity = "X" if issue.severity == "block" else "!"
            print(f"    {severity} [{issue.code}] {issue.message}")

    print()


def cmd_content_qc_captions(args):
    """Run caption WER QC hook."""
    import asyncio
    from atlas.orchestrator.hooks import HookRunner

    print(f"\n=== CAPTION WER QC ===\n")
    print(f"  Video: {args.video}")
    print(f"  SRT: {args.srt}")
    print()

    runner = HookRunner()
    cli_args = ["--video", args.video, "--srt", args.srt]

    result = asyncio.run(runner.run(
        "babybrains_content",
        "qc_caption_wer",
        cli_args=cli_args,
    ))

    if result.passed:
        print("  [PASS] Caption WER within threshold")
    else:
        print("  [FAIL] Caption WER too high")
        for issue in result.issues:
            severity = "X" if issue.severity == "block" else "!"
            print(f"    {severity} [{issue.code}] {issue.message}")

    print()


def cmd_content_qc_safezone(args):
    """Run caption safe zone QC hook."""
    import asyncio
    from atlas.orchestrator.hooks import HookRunner

    print(f"\n=== SAFE ZONE QC ===\n")
    print(f"  Subtitle: {args.subtitle}")
    print(f"  Platform: {args.platform}")
    print()

    runner = HookRunner()
    cli_args = ["--subtitle", args.subtitle, "--platform", args.platform]

    result = asyncio.run(runner.run(
        "babybrains_content",
        "qc_safezone",
        cli_args=cli_args,
    ))

    if result.passed:
        print("  [PASS] Captions within safe zones")
    else:
        print("  [FAIL] Safe zone violations detected")
        for issue in result.issues:
            severity = "X" if issue.severity == "block" else "!"
            print(f"    {severity} [{issue.code}] {issue.message}")

    print()


def cmd_content_status(args):
    """Show content pipeline status."""
    conn = get_conn()
    db.run_content_migration(conn)

    runs = db.get_all_pipeline_runs(conn, limit=20)
    draft_briefs = db.get_briefs_by_status(conn, "draft", limit=10)

    print(f"\n=== CONTENT PIPELINE STATUS ===\n")

    # Draft briefs
    print(f"  DRAFT BRIEFS: {len(draft_briefs)}")
    for b in draft_briefs[:5]:
        print(f"    #{b['id']} {b['topic'][:40]}")

    # Pipeline runs
    if runs:
        print(f"\n  PIPELINE RUNS:")
        active = [r for r in runs if not r.is_complete and not r.is_failed]
        waiting = [r for r in runs if r.is_waiting_for_human]
        failed = [r for r in runs if r.is_failed]
        complete = [r for r in runs if r.is_complete]

        print(f"    Active: {len(active)}")
        print(f"    Waiting for human: {len(waiting)}")
        print(f"    Failed: {len(failed)}")
        print(f"    Complete: {len(complete)}")

        if active:
            print(f"\n    ACTIVE RUNS:")
            for r in active[:5]:
                print(f"      #{r.id} Stage: {r.current_stage} (retry {r.retry_count}/{r.max_retries})")

        if waiting:
            print(f"\n    WAITING FOR HUMAN:")
            for r in waiting[:5]:
                print(f"      #{r.id} Gate: {r.current_stage}")
                print(f"         Resume: content gate-complete --run-id {r.id} --gate {r.current_stage}")

        if failed:
            print(f"\n    FAILED RUNS:")
            for r in failed[:3]:
                print(f"      #{r.id} Stage: {r.current_stage}")
                if r.hook_failures:
                    for hf in r.hook_failures[:2]:
                        print(f"         [{hf.get('code')}] {hf.get('msg', '')[:50]}")
    else:
        print(f"\n  No pipeline runs yet.")
        print(f"  Start with: python -m atlas.babybrains.cli content brief --topic 'Topic' --age '0-6m'")

    print()
    conn.close()


def cmd_content_resume(args):
    """Resume a paused pipeline run."""
    conn = get_conn()
    db.run_content_migration(conn)

    run = db.get_pipeline_run(conn, args.run_id)
    if not run:
        print(f"Error: Pipeline run {args.run_id} not found")
        conn.close()
        return

    print(f"\n=== RESUME PIPELINE RUN #{args.run_id} ===\n")
    print(f"  Current stage: {run.current_stage}")
    print(f"  Brief ID: {run.brief_id}")
    print(f"  Script ID: {run.script_id}")
    print(f"  Retries: {run.retry_count}/{run.max_retries}")
    print()

    if run.is_failed:
        print("  Status: FAILED")
        print("  To retry, use: content update-script --script-id N --file /path")
    elif run.is_waiting_for_human:
        print(f"  Status: WAITING FOR HUMAN ({run.current_stage})")
        print(f"  Complete gate: content gate-complete --run-id {args.run_id} --gate {run.current_stage}")
    else:
        print("  Status: Can resume from current stage")
        print("  NOTE: Pipeline orchestrator not yet implemented.")
        print("  This would continue the pipeline from the current stage.")

    print()
    conn.close()


def cmd_content_gate_complete(args):
    """Mark a manual gate as complete."""
    conn = get_conn()
    db.run_content_migration(conn)

    run = db.get_pipeline_run(conn, args.run_id)
    if not run:
        print(f"Error: Pipeline run {args.run_id} not found")
        conn.close()
        return

    valid_gates = {"manual_visual", "manual_visual_qc", "manual_assembly", "review"}
    if args.gate not in valid_gates:
        print(f"Error: Invalid gate '{args.gate}'. Valid gates: {valid_gates}")
        conn.close()
        return

    if run.current_stage != args.gate:
        print(f"Error: Run #{args.run_id} is at stage '{run.current_stage}', not '{args.gate}'")
        conn.close()
        return

    # Advance to next stage
    stage_order = [
        "brief", "brief_qc", "script", "script_qc", "localise", "prompts",
        "manual_visual", "manual_visual_qc", "manual_assembly", "assembly_qc",
        "review", "captions", "complete"
    ]
    current_idx = stage_order.index(args.gate)
    next_stage = stage_order[current_idx + 1] if current_idx < len(stage_order) - 1 else "complete"

    db.update_pipeline_run(conn, args.run_id, current_stage=next_stage)

    print(f"\n=== GATE COMPLETE ===\n")
    print(f"  Run ID: {args.run_id}")
    print(f"  Completed gate: {args.gate}")
    print(f"  New stage: {next_stage}")
    print()
    conn.close()


def cmd_content_update_script(args):
    """Update a script from a file (for retry after failure)."""
    conn = get_conn()
    db.run_content_migration(conn)

    script = db.get_script_by_id(conn, args.script_id)
    if not script:
        print(f"Error: Script {args.script_id} not found")
        conn.close()
        return

    script_path = Path(args.file)
    if not script_path.exists():
        print(f"Error: File not found: {args.file}")
        conn.close()
        return

    new_content = json.loads(script_path.read_text())

    # Update script fields from file
    update_fields = {}
    if "scenes" in new_content:
        update_fields["scenes"] = new_content["scenes"]
    if "script_text" in new_content:
        update_fields["script_text"] = new_content["script_text"]
    if "word_count" in new_content:
        update_fields["word_count"] = new_content["word_count"]
    if "voiceover" in new_content:
        update_fields["voiceover"] = new_content["voiceover"]

    if update_fields:
        db.update_script_fields(conn, args.script_id, **update_fields)
        print(f"\n=== SCRIPT UPDATED ===\n")
        print(f"  Script ID: {args.script_id}")
        print(f"  Updated fields: {', '.join(update_fields.keys())}")
        print(f"\n  Now re-run QC: content qc --script-id {args.script_id}")
    else:
        print(f"Error: No valid fields found in {args.file}")

    print()
    conn.close()


# ============================================
# TRENDS COMMANDS (S2.6-lite)
# ============================================


def cmd_trends_scan(args):
    """Scan for trending parenting content opportunities."""
    import asyncio

    logging.basicConfig(level=logging.INFO, format="  %(message)s")

    from atlas.babybrains.trends.engine import TrendService

    conn = get_conn()
    db.run_trends_migration(conn)

    service = TrendService(conn=conn)

    print(f"\n=== TREND SCAN ===\n")

    # Check budget first
    budget = service.get_budget_status()
    if not budget["budget_ok"]:
        print(f"  Budget exceeded!")
        print(f"  Daily: ${budget['daily']['used']:.2f} / ${budget['daily']['limit']:.2f}")
        print(f"  Monthly: ${budget['monthly']['used']:.2f} / ${budget['monthly']['limit']:.2f}")
        print()
        return

    print(f"  Focus: {args.focus or 'general'}")
    print(f"  Max topics: {args.max}")
    print()

    result = asyncio.run(service.scan(
        niche_focus=args.focus,
        max_topics=args.max,
    ))

    print(f"  Source: {result.source}")
    print(f"  Cost: ${result.cost_usd:.4f}")
    if result.filtered_count > 0:
        print(f"  Filtered (brand safety): {result.filtered_count}")
    if result.reason:
        print(f"  Note: {result.reason}")
    print()

    if result.topics:
        print(f"  TOPICS FOUND ({len(result.topics)}):")
        for i, t in enumerate(result.topics, 1):
            level_marker = {"urgent": "!!!", "high": "!!", "medium": "!", "low": ""}.get(
                t.opportunity_level, ""
            )
            print(f"    {i}. {t.topic} [{t.opportunity_level}]{level_marker}")
            print(f"       Score: {t.score:.2f} | Confidence: {t.confidence:.2f}")
            if t.description:
                print(f"       {t.description[:80]}...")
            if t.content_angle:
                print(f"       Angle: {t.content_angle[:60]}...")
            print()
    else:
        print("  No topics found.")

    print()
    conn.close()


def cmd_trends_latest(args):
    """Show latest stored trends."""
    import asyncio

    from atlas.babybrains.trends.engine import TrendService

    conn = get_conn()
    db.run_trends_migration(conn)

    service = TrendService(conn=conn)
    trends = asyncio.run(service.get_latest(limit=args.limit))

    print(f"\n=== LATEST TRENDS ({len(trends)}) ===\n")

    if not trends:
        print("  No trends stored yet.")
        print("  Run: python -m atlas.babybrains.cli trends scan")
    else:
        for i, t in enumerate(trends, 1):
            sources = ", ".join(t.sources)
            print(f"  {i}. {t.topic}")
            print(f"     Score: {t.score:.2f} | Level: {t.opportunity_level} | Source: {sources}")
            if t.audience_segment:
                print(f"     Segment: {t.audience_segment}")
            print()

    print()
    conn.close()


def cmd_trends_budget(args):
    """Show Grok API budget status."""
    from atlas.babybrains.trends.engine import TrendService

    conn = get_conn()
    db.run_trends_migration(conn)

    service = TrendService(conn=conn)
    status = service.get_budget_status()

    print(f"\n=== GROK BUDGET STATUS ===\n")

    daily = status["daily"]
    monthly = status["monthly"]

    print(f"  DAILY:")
    print(f"    Used: ${daily['used']:.4f} / ${daily['limit']:.2f}")
    print(f"    Remaining: ${daily['remaining']:.4f}")
    print(f"    Operations: {daily['operations']}")

    print(f"\n  MONTHLY:")
    print(f"    Used: ${monthly['used']:.4f} / ${monthly['limit']:.2f}")
    print(f"    Remaining: ${monthly['remaining']:.4f}")
    print(f"    Operations: {monthly['operations']}")

    if not status["budget_ok"]:
        print(f"\n  STATUS: BUDGET EXCEEDED")
    elif status["budget_warning"]:
        print(f"\n  STATUS: WARNING - Low budget remaining")
    else:
        print(f"\n  STATUS: OK")

    print()
    conn.close()


def cmd_trends_suggest(args):
    """Suggest high-value topics for content creation."""
    import asyncio

    from atlas.babybrains.trends.engine import TrendService

    conn = get_conn()
    db.run_trends_migration(conn)

    service = TrendService(conn=conn)
    suggestions = asyncio.run(service.suggest_topics_for_content(n=args.n))

    print(f"\n=== CONTENT SUGGESTIONS ({len(suggestions)}) ===\n")

    if not suggestions:
        print("  No suggestions available.")
        print("  Run: python -m atlas.babybrains.cli trends scan")
    else:
        for i, t in enumerate(suggestions, 1):
            kg_marker = "[KB]" if t.knowledge_graph_match else ""
            print(f"  {i}. {t.topic} {kg_marker}")
            print(f"     Score: {t.score:.2f} | Confidence: {t.confidence:.2f} | Level: {t.opportunity_level}")
            if t.content_angle:
                print(f"     Angle: {t.content_angle[:70]}...")
            if t.audience_segment:
                print(f"     Target: {t.audience_segment}")
            print()

    print()
    conn.close()


def cmd_content_pipeline(args):
    """Run the full content pipeline (placeholder)."""
    conn = get_conn()
    db.run_content_migration(conn)

    # Check if we have a brief
    if args.brief_id:
        brief = db.get_brief_by_id(conn, args.brief_id)
        if not brief:
            print(f"Error: Brief {args.brief_id} not found")
            conn.close()
            return
    else:
        # Create a new brief
        if not args.topic:
            print("Error: Either --brief-id or --topic is required")
            conn.close()
            return

        brief_id = db.add_content_brief(
            conn,
            topic=args.topic,
            age_range=args.age,
            montessori_principle=args.principle,
            target_length=args.length,
        )
        brief = db.get_brief_by_id(conn, brief_id)
        print(f"Created brief #{brief_id}: {args.topic}")

    # Create pipeline run
    run_id = db.add_pipeline_run(conn, brief.id, current_stage="brief", max_retries=args.max_retries)

    print(f"\n=== CONTENT PIPELINE STARTED ===\n")
    print(f"  Run ID: {run_id}")
    print(f"  Brief ID: {brief.id}")
    print(f"  Topic: {brief.topic}")
    print(f"  Age range: {brief.age_range}")
    print(f"  Target length: {brief.target_length}")
    print(f"  Max retries: {args.max_retries}")
    print()
    print("  NOTE: Full pipeline orchestrator not yet implemented.")
    print("  The pipeline would proceed through these stages:")
    print("    1. brief_qc -> Validate brief structure")
    print("    2. script -> Generate script using bb_script_write skill")
    print("    3. script_qc -> Run qc_script, qc_safety, qc_montessori hooks")
    print("    4. localise -> Add AU visual cues using bb_au_localise skill")
    print("    5. prompts -> Generate MJ/Pika/Kling prompts")
    print("    6. manual_visual -> Human generates visuals (MANUAL GATE)")
    print("    7. manual_visual_qc -> Human reviews visuals (MANUAL GATE)")
    print("    8. manual_assembly -> Human assembles in DaVinci (MANUAL GATE)")
    print("    9. assembly_qc -> Run qc_audio, qc_caption_wer hooks")
    print("   10. review -> Human final review (MANUAL GATE)")
    print("   11. captions -> Generate platform captions")
    print("   12. complete -> Pipeline done")
    print()
    print(f"  Track progress: content status")
    print(f"  Resume if stuck: content resume --run-id {run_id}")

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

    # warming run (prep + watch in one go)
    wr = warming_sub.add_parser("run", help="Full daily warming: generate targets + watch")
    wr.add_argument("--platform", default="youtube", help="Platform (default: youtube)")

    # warming prep
    wp = warming_sub.add_parser("prep", help="Generate today's targets from YouTube API")
    wp.add_argument("--platform", default="youtube", help="Platform (default: youtube)")

    # warming daily
    wd = warming_sub.add_parser("daily", help="Show today's targets")
    wd.add_argument("--platform", help="Filter by platform")

    # warming watch
    ww = warming_sub.add_parser("watch", help="Run automated browser warming session")
    ww.add_argument("--platform", default="youtube", help="Platform to warm (default: youtube)")

    # warming done
    wdone = warming_sub.add_parser("done", help="Log completed actions")
    wdone.add_argument("platform", help="Platform name")
    wdone.add_argument("actions", nargs="+", help="Actions (e.g., '3 comments 2 likes')")

    # warming status
    ws = warming_sub.add_parser("status", help="Show warming stats")
    ws.add_argument("--days", type=int, default=7, help="Days to look back")

    # content
    content = subparsers.add_parser("content", help="Content production pipeline commands")
    content_sub = content.add_subparsers(dest="content_command")

    # content brief
    cb = content_sub.add_parser("brief", help="Create a content brief")
    cb.add_argument("--topic", required=True, help="Brief topic/title")
    cb.add_argument("--age", required=True, help="Age range (0-6m, 6-12m, 12-24m, 24-36m)")
    cb.add_argument("--principle", help="Primary Montessori principle slug")
    cb.add_argument("--length", default="60s", help="Target length (21s, 60s, 90s)")
    cb.add_argument("--pillar", help="Content pillar")

    # content script
    cs = content_sub.add_parser("script", help="Generate script for a brief")
    cs.add_argument("--brief-id", type=int, required=True, help="Brief ID")
    cs.add_argument("--template", default="core_educational", help="Script template type")

    # content localise
    cl = content_sub.add_parser("localise", help="Add AU localisation to script")
    cl.add_argument("--script-id", type=int, required=True, help="Script ID")

    # content prompts
    cp = content_sub.add_parser("prompts", help="Generate visual prompts")
    cp.add_argument("--script-id", type=int, required=True, help="Script ID")
    cp.add_argument("--tool", default="midjourney", choices=["midjourney", "pika", "kling"], help="Generation tool")

    # content qc
    cq = content_sub.add_parser("qc", help="Run QC hooks on a script")
    cq.add_argument("--script-id", type=int, required=True, help="Script ID")

    # content qc-audio
    cqa = content_sub.add_parser("qc-audio", help="Run audio QC on a file")
    cqa.add_argument("--file", required=True, help="Audio/video file path")
    cqa.add_argument("--master", action="store_true", help="Use master audio thresholds")

    # content qc-captions
    cqc = content_sub.add_parser("qc-captions", help="Run caption WER QC")
    cqc.add_argument("--video", required=True, help="Video file path")
    cqc.add_argument("--srt", required=True, help="SRT subtitle file path")

    # content qc-safezone
    cqs = content_sub.add_parser("qc-safezone", help="Run caption safe zone QC")
    cqs.add_argument("--subtitle", required=True, help="Subtitle file path (ASS or VTT)")
    cqs.add_argument("--platform", required=True, choices=["tiktok", "instagram_reels", "youtube_shorts", "facebook_reels"], help="Target platform")

    # content status
    content_sub.add_parser("status", help="Show pipeline status")

    # content resume
    cr = content_sub.add_parser("resume", help="Resume a paused pipeline run")
    cr.add_argument("--run-id", type=int, required=True, help="Pipeline run ID")

    # content gate-complete
    cg = content_sub.add_parser("gate-complete", help="Mark a manual gate as complete")
    cg.add_argument("--run-id", type=int, required=True, help="Pipeline run ID")
    cg.add_argument("--gate", required=True, help="Gate name (manual_visual, manual_visual_qc, manual_assembly, review)")

    # content update-script
    cu = content_sub.add_parser("update-script", help="Update script from file")
    cu.add_argument("--script-id", type=int, required=True, help="Script ID")
    cu.add_argument("--file", required=True, help="JSON file with script updates")

    # content pipeline
    cpp = content_sub.add_parser("pipeline", help="Run full content pipeline")
    cpp.add_argument("--brief-id", type=int, help="Existing brief ID")
    cpp.add_argument("--topic", help="Topic for new brief")
    cpp.add_argument("--age", help="Age range for new brief")
    cpp.add_argument("--principle", help="Montessori principle for new brief")
    cpp.add_argument("--length", default="60s", help="Target length for new brief")
    cpp.add_argument("--max-retries", type=int, default=3, help="Max retries per stage")

    # trends (S2.6-lite)
    trends = subparsers.add_parser("trends", help="Trend detection commands")
    trends_sub = trends.add_subparsers(dest="trends_command")

    # trends scan
    ts = trends_sub.add_parser("scan", help="Scan for trending topics")
    ts.add_argument("--focus", help="Niche focus area (e.g., 'emerging', 'conversations')")
    ts.add_argument("--max", type=int, default=10, help="Max topics to return")

    # trends latest
    tl = trends_sub.add_parser("latest", help="Show latest stored trends")
    tl.add_argument("--limit", type=int, default=10, help="Max trends to show")

    # trends budget
    trends_sub.add_parser("budget", help="Show Grok API budget status")

    # trends suggest
    tsg = trends_sub.add_parser("suggest", help="Suggest topics for content")
    tsg.add_argument("-n", type=int, default=5, help="Number of suggestions")

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
        if args.warming_command == "run":
            cmd_warming_run(args)
        elif args.warming_command == "prep":
            cmd_warming_prep(args)
        elif args.warming_command == "daily":
            cmd_warming_daily(args)
        elif args.warming_command == "watch":
            cmd_warming_watch(args)
        elif args.warming_command == "done":
            cmd_warming_done(args)
        elif args.warming_command == "status":
            cmd_warming_status(args)
        else:
            warming.print_help()
    elif args.command == "content":
        if args.content_command == "brief":
            cmd_content_brief(args)
        elif args.content_command == "script":
            cmd_content_script(args)
        elif args.content_command == "localise":
            cmd_content_localise(args)
        elif args.content_command == "prompts":
            cmd_content_prompts(args)
        elif args.content_command == "qc":
            cmd_content_qc(args)
        elif args.content_command == "qc-audio":
            cmd_content_qc_audio(args)
        elif args.content_command == "qc-captions":
            cmd_content_qc_captions(args)
        elif args.content_command == "qc-safezone":
            cmd_content_qc_safezone(args)
        elif args.content_command == "status":
            cmd_content_status(args)
        elif args.content_command == "resume":
            cmd_content_resume(args)
        elif args.content_command == "gate-complete":
            cmd_content_gate_complete(args)
        elif args.content_command == "update-script":
            cmd_content_update_script(args)
        elif args.content_command == "pipeline":
            cmd_content_pipeline(args)
        else:
            content.print_help()
    elif args.command == "trends":
        if args.trends_command == "scan":
            cmd_trends_scan(args)
        elif args.trends_command == "latest":
            cmd_trends_latest(args)
        elif args.trends_command == "budget":
            cmd_trends_budget(args)
        elif args.trends_command == "suggest":
            cmd_trends_suggest(args)
        else:
            trends.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
