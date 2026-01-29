#!/usr/bin/env python3
"""
ATLAS Health CLI

Command-line interface for health and fitness tracking.

Commands:
    atlas-health daily         - Morning sync + show today's workout
    atlas-health workout       - View/log workouts
    atlas-health supplements   - Supplement checklist
    atlas-health weight        - Weight tracking
    atlas-health stats         - Health statistics
    atlas-health pain          - Pain tracking
    atlas-health routine       - Daily morning routine
    atlas-health assess        - Fitness assessments and GATE checks
    atlas-health phase         - Training phase management
    atlas-health garmin        - Garmin Connect integration

Examples:
    atlas-health daily                           # Show today's status
    atlas-health daily --sleep 7.2 --hrv BALANCED  # Manual metrics input
    atlas-health workout                         # Show today's workout
    atlas-health workout log --duration 45       # Log completed workout
    atlas-health supplements                     # Show checklist
    atlas-health supplements check "Vitamin D"   # Mark as taken
    atlas-health supplements add "Creatine" --dosage "5g" --timing morning
    atlas-health weight                          # Show recent weights
    atlas-health weight log 82.3                 # Log weight
    atlas-health weight log 82.3 --bf 18.5       # Log weight + body fat
    atlas-health weight trend                    # 7-day trend
    atlas-health stats --week                    # Weekly stats
    atlas-health routine                         # Show morning routine
    atlas-health routine start                   # Interactive guided routine
    atlas-health routine log                     # Log routine completion
    atlas-health assess                          # List available assessments
    atlas-health assess baseline                 # Show baseline testing protocol
    atlas-health assess log --id ankle_dorsiflexion_left --value 9.5
    atlas-health assess progress                 # Show progress from baseline
    atlas-health assess gate 1                   # Check GATE 1 readiness
    atlas-health phase                           # Show current phase status
    atlas-health phase check                     # Check if ready to advance
    atlas-health phase advance                   # Advance to next phase
    atlas-health phase start                     # Start Phase 1
    atlas-health garmin status                   # Check Garmin connection
    atlas-health garmin sync                     # Sync today's Garmin data

Usage:
    python -m atlas.health.cli daily
    python -m atlas.health.cli workout
    python -m atlas.health.cli supplements
    python -m atlas.health.cli weight
    python -m atlas.health.cli routine
"""

import argparse
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from atlas.health.router import TrafficLightRouter, TrafficLightStatus
from atlas.health.workout import WorkoutService
from atlas.health.supplement import SupplementService
from atlas.health.assessment import AssessmentService
from atlas.health.phase import PhaseService
from atlas.health.workout_lookup import (
    get_todays_workout,
    get_current_week,
    is_deload_week,
    format_workout_display,
    format_workout_voice,
)


def load_daily_routine() -> Optional[dict]:
    """Load daily routine from phase config."""
    config_path = Path(__file__).parent.parent.parent / "config" / "workouts" / "phase1.json"
    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_path}: {e}")
        return None

    return config.get("daily_routine")


def cmd_daily(args: argparse.Namespace) -> None:
    """Morning sync and daily status."""
    router = TrafficLightRouter()
    workout_service = WorkoutService()
    supplement_service = SupplementService()

    # Get metrics (manual input or from Garmin when available)
    sleep_hours = args.sleep
    hrv_status = args.hrv
    resting_hr = args.rhr

    # Evaluate traffic light
    result = router.evaluate(
        sleep_hours=sleep_hours,
        hrv_status=hrv_status,
        resting_hr=resting_hr,
    )

    # Get today's workout
    workout_plan = workout_service.get_todays_workout(traffic_light=result.status)

    # Get supplement status
    checklist = supplement_service.get_today()

    # Display
    emoji = router.get_day_emoji(result.status)
    status_name = result.status.value.upper()

    print()
    print("\u2554" + "\u2550" * 58 + "\u2557")
    print(f"\u2551  ATLAS Daily - {date.today().strftime('%B %d, %Y'):<40} \u2551")
    print("\u2560" + "\u2550" * 58 + "\u2563")

    # Traffic Light status
    if sleep_hours or hrv_status or resting_hr:
        metrics = []
        if sleep_hours:
            metrics.append(f"Sleep: {sleep_hours}h")
        if hrv_status:
            metrics.append(f"HRV: {hrv_status}")
        if resting_hr:
            metrics.append(f"RHR: {resting_hr}")
        metrics_str = " | ".join(metrics)
        print(f"\u2551  {emoji} {status_name} DAY{' ' * (48 - len(status_name))} \u2551")
        print(f"\u2551  {metrics_str:<56} \u2551")
    else:
        print(f"\u2551  {emoji} {status_name} DAY (no metrics provided){' ' * (32 - len(status_name))} \u2551")
        print(f"\u2551  Use --sleep, --hrv, --rhr for manual input{' ' * 13} \u2551")

    print("\u2560" + "\u2550" * 58 + "\u2563")

    # Today's workout
    if workout_plan:
        day_names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        day_name = day_names[date.today().weekday()]  # Use actual date, not protocol
        print(f"\u2551  TODAY: {day_name} - {workout_plan.protocol.name:<38} \u2551")
        if workout_plan.is_red_day_override:
            print(f"\u2551  \u26A0\uFE0F  RED DAY OVERRIDE - Recovery only{' ' * 19} \u2551")
    else:
        print(f"\u2551  TODAY: No scheduled workout{' ' * 28} \u2551")

    print("\u2560" + "\u2550" * 58 + "\u2563")

    # Supplement status
    taken = checklist.taken_count
    total = checklist.total
    pct = checklist.completion_pct
    print(f"\u2551  SUPPLEMENTS: {taken}/{total} taken ({pct:.0f}%){' ' * (36 - len(str(taken)) - len(str(total)))} \u2551")

    # Quick list of pending
    pending = [s.name for s in checklist.supplements if not s.taken][:3]
    if pending:
        pending_str = ", ".join(pending)
        if len(pending_str) > 50:
            pending_str = pending_str[:47] + "..."
        print(f"\u2551  Pending: {pending_str:<47} \u2551")

    print("\u255A" + "\u2550" * 58 + "\u255D")

    # Recommendation
    print()
    print(f"Recommendation: {result.recommendation}")
    print()


def cmd_workout(args: argparse.Namespace) -> None:
    """Workout commands."""
    service = WorkoutService()
    router = TrafficLightRouter()

    if args.action == "show":
        # Determine traffic light from args
        if args.red:
            status = TrafficLightStatus.RED
        elif args.yellow:
            status = TrafficLightStatus.YELLOW
        else:
            status = TrafficLightStatus.GREEN

        plan = service.get_todays_workout(traffic_light=status)
        if plan:
            print(plan.to_display())
        else:
            print("No workout scheduled for today.")

    elif args.action == "log":
        if not args.duration:
            print("Error: --duration is required")
            print("Usage: atlas-health workout log --duration 45")
            sys.exit(1)

        workout_id = service.log_completed(
            duration_minutes=args.duration,
            workout_type=args.type,
            energy_before=args.energy_before,
            energy_after=args.energy_after,
            notes=args.notes,
        )
        print(f"\u2713 Logged workout #{workout_id}")
        print(f"  Duration: {args.duration} min")
        if args.type:
            print(f"  Type: {args.type}")
        if args.energy_before:
            print(f"  Energy before: {args.energy_before}/10")
        if args.energy_after:
            print(f"  Energy after: {args.energy_after}/10")

    elif args.action == "history":
        history = service.get_workout_history(days=args.days or 14)
        if not history:
            print("No workouts logged recently.")
            return

        print(f"\nWorkout History (last {args.days or 14} days):")
        print("-" * 50)
        for w in history:
            date_str = w["date"]
            type_str = w["type"] or "workout"
            duration = w["duration_minutes"] or 0
            energy = ""
            if w["energy_before"] and w["energy_after"]:
                energy = f" (energy: {w['energy_before']}\u2192{w['energy_after']})"
            print(f"  {date_str}: {type_str:<12} {duration}min{energy}")


def cmd_supplements(args: argparse.Namespace) -> None:
    """Supplement tracking."""
    service = SupplementService()

    if args.action == "show":
        checklist = service.get_today()
        print(checklist.to_display())

    elif args.action == "check":
        if not args.name:
            print("Error: supplement name required")
            print("Usage: atlas-health supplements check \"Vitamin D\"")
            sys.exit(1)

        success = service.mark_taken(args.name)
        if success:
            print(f"\u2713 Marked '{args.name}' as taken")
        else:
            print(f"\u2717 Supplement not found: '{args.name}'")
            print("\nAvailable supplements:")
            for s in service.get_active_supplements():
                print(f"  - {s.name}")

    elif args.action == "all-morning":
        count = service.mark_all_taken(timing="morning")
        print(f"\u2713 Marked {count} morning supplements as taken")

    elif args.action == "all-evening":
        count = service.mark_all_taken(timing="before_bed")
        print(f"\u2713 Marked {count} evening supplements as taken")

    elif args.action == "add":
        if not args.name:
            print("Error: supplement name required")
            print("Usage: atlas-health supplements add \"Vitamin D\" --dosage \"5000 IU\" --timing morning")
            sys.exit(1)

        supp_id = service.add_supplement(
            name=args.name,
            dosage=args.dosage,
            timing=args.timing,
            purpose=args.purpose,
            brand=args.brand,
        )
        print(f"\u2713 Added supplement: {args.name} (ID: {supp_id})")

    elif args.action == "list":
        supplements = service.get_active_supplements()
        if not supplements:
            print("No supplements configured.")
            print("Add one with: atlas-health supplements add \"Vitamin D\" --dosage \"5000 IU\"")
            return

        print("\nActive Supplements:")
        print("-" * 50)
        for s in supplements:
            dosage = f"({s.dosage})" if s.dosage else ""
            timing = f"[{s.timing}]" if s.timing else ""
            print(f"  {s.name:<25} {dosage:<15} {timing}")


def cmd_pain(args: argparse.Namespace) -> None:
    """Pain tracking."""
    import sqlite3
    from pathlib import Path

    db_path = Path.home() / ".atlas" / "atlas.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    today = date.today()

    if args.action == "log":
        # Validate required arguments
        if not args.body_part:
            print("Error: body_part required")
            print("Usage: atlas-health pain log <body_part> --level <0-10>")
            print("Valid body parts: shoulder_right, feet, ankle_left, ankle_right, lower_back")
            conn.close()
            sys.exit(1)
        if args.level is None:
            print("Error: --level required")
            print("Usage: atlas-health pain log shoulder_right --level 5")
            conn.close()
            sys.exit(1)

        # Log pain for a body part
        body_part = args.body_part
        pain = args.level

        conn.execute("""
            INSERT OR REPLACE INTO pain_log (date, body_part, pain_level, notes)
            VALUES (?, ?, ?, ?)
        """, (today.isoformat(), body_part, pain, args.notes))
        conn.commit()

        emoji = "\U0001F7E2" if pain <= 2 else ("\U0001F7E1" if pain <= 5 else "\U0001F534")
        print(f"{emoji} Logged {body_part}: {pain}/10")

    elif args.action == "all":
        # Quick log all body parts
        body_parts = ["shoulder_right", "feet", "ankle_left", "ankle_right", "lower_back"]
        print("\nLog pain levels (0-10) for each area:")
        print("-" * 40)

        for bp in body_parts:
            while True:
                try:
                    level = input(f"  {bp}: ")
                    if level == "":
                        level = 0
                    else:
                        level = int(level)
                    if 0 <= level <= 10:
                        break
                    print("    Enter 0-10")
                except ValueError:
                    print("    Enter a number 0-10")

            conn.execute("""
                INSERT OR REPLACE INTO pain_log (date, body_part, pain_level)
                VALUES (?, ?, ?)
            """, (today.isoformat(), bp, level))

        conn.commit()
        print("\n\u2713 All pain levels logged")

    else:  # show (default)
        cursor = conn.execute("""
            SELECT body_part, pain_level, notes
            FROM pain_log WHERE date = ?
        """, (today.isoformat(),))

        rows = cursor.fetchall()

        print()
        print("=" * 50)
        print(f"  PAIN LOG - {today.strftime('%B %d, %Y')}")
        print("=" * 50)

        if not rows:
            print("\n  No pain logged today.")
            print("  Use: atlas-health pain all")
        else:
            for row in rows:
                level = row["pain_level"]
                emoji = "\U0001F7E2" if level <= 2 else ("\U0001F7E1" if level <= 5 else "\U0001F534")
                notes = f" - {row['notes']}" if row["notes"] else ""
                print(f"  {emoji} {row['body_part']:<20} {level}/10{notes}")

        print("=" * 50)

    conn.close()


def cmd_weight(args: argparse.Namespace) -> None:
    """Weight tracking commands."""
    import sqlite3
    from pathlib import Path
    from datetime import datetime, timedelta

    db_path = Path.home() / ".atlas" / "atlas.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Ensure table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weight_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            time TIME,
            weight_kg REAL NOT NULL CHECK(weight_kg BETWEEN 20 AND 300),
            body_fat_pct REAL CHECK(body_fat_pct IS NULL OR body_fat_pct BETWEEN 1 AND 70),
            source VARCHAR(20) DEFAULT 'manual',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, time)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_log_date ON weight_log(date DESC)")
    conn.commit()

    today = date.today()
    now = datetime.now()

    if args.action == "log":
        if args.weight is None:
            print("Error: weight value required")
            print("Usage: atlas-health weight log 82.3")
            print("       atlas-health weight log 82.3 --bf 18.5")
            conn.close()
            sys.exit(1)

        weight = args.weight
        body_fat = args.bf
        current_time = now.strftime("%H:%M")

        # Validate ranges
        if weight < 20 or weight > 300:
            print(f"Error: Weight {weight}kg outside valid range (20-300kg)")
            conn.close()
            sys.exit(1)

        if body_fat is not None and (body_fat < 1 or body_fat > 70):
            print(f"Error: Body fat {body_fat}% outside valid range (1-70%)")
            conn.close()
            sys.exit(1)

        # Insert or update today's entry
        conn.execute("""
            INSERT INTO weight_log (date, time, weight_kg, body_fat_pct, source, notes)
            VALUES (?, ?, ?, ?, 'manual', ?)
            ON CONFLICT(date, time) DO UPDATE SET
                weight_kg = excluded.weight_kg,
                body_fat_pct = excluded.body_fat_pct,
                notes = excluded.notes
        """, (today.isoformat(), current_time, weight, body_fat, args.notes))
        conn.commit()

        bf_str = f", {body_fat}% BF" if body_fat else ""
        print(f"\u2713 Logged: {weight}kg{bf_str}")

        # Show comparison to yesterday
        yesterday = (today - timedelta(days=1)).isoformat()
        cursor = conn.execute("""
            SELECT weight_kg FROM weight_log
            WHERE date = ? ORDER BY time DESC LIMIT 1
        """, (yesterday,))
        row = cursor.fetchone()
        if row:
            diff = weight - row["weight_kg"]
            direction = "+" if diff >= 0 else ""
            print(f"  vs yesterday: {direction}{diff:.1f}kg")

    elif args.action == "trend":
        days = args.days or 7
        start_date = (today - timedelta(days=days)).isoformat()

        cursor = conn.execute("""
            SELECT date, weight_kg, body_fat_pct
            FROM weight_log
            WHERE date >= ?
            ORDER BY date ASC, time ASC
        """, (start_date,))
        rows = cursor.fetchall()

        if not rows:
            print(f"No weight data in last {days} days.")
            print("Log with: atlas-health weight log 82.3")
            conn.close()
            return

        # Calculate stats
        weights = [r["weight_kg"] for r in rows]
        avg_weight = sum(weights) / len(weights)
        min_weight = min(weights)
        max_weight = max(weights)

        first_weight = weights[0]
        last_weight = weights[-1]
        change = last_weight - first_weight

        print()
        print("=" * 50)
        print(f"  WEIGHT TREND - Last {days} days")
        print("=" * 50)
        print()
        print(f"  Current:  {last_weight:.1f} kg")
        print(f"  Average:  {avg_weight:.1f} kg")
        print(f"  Range:    {min_weight:.1f} - {max_weight:.1f} kg")
        print()
        direction = "+" if change >= 0 else ""
        trend_word = "up" if change > 0.2 else ("down" if change < -0.2 else "stable")
        print(f"  Change:   {direction}{change:.1f} kg ({trend_word})")
        print()

        # Show daily entries
        print("-" * 50)
        for row in rows[-7:]:  # Last 7 entries max
            bf_str = f" | {row['body_fat_pct']:.1f}% BF" if row["body_fat_pct"] else ""
            print(f"  {row['date']}: {row['weight_kg']:.1f} kg{bf_str}")
        print("=" * 50)

    else:  # show (default)
        # Show recent entries
        cursor = conn.execute("""
            SELECT date, time, weight_kg, body_fat_pct
            FROM weight_log
            ORDER BY date DESC, time DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()

        print()
        print("=" * 50)
        print("  WEIGHT LOG - Recent Entries")
        print("=" * 50)

        if not rows:
            print()
            print("  No weight data logged yet.")
            print("  Log with: atlas-health weight log 82.3")
        else:
            print()
            for row in rows:
                time_str = f" {row['time']}" if row["time"] else ""
                bf_str = f" | {row['body_fat_pct']:.1f}% BF" if row["body_fat_pct"] else ""
                print(f"  {row['date']}{time_str}: {row['weight_kg']:.1f} kg{bf_str}")

        print()
        print("=" * 50)
        print("  Commands: weight log <kg> | weight trend")
        print()

    conn.close()


def cmd_cardio(args: argparse.Namespace) -> None:
    """Cardio session logging."""
    import sqlite3
    from datetime import datetime, timedelta

    db_path = Path.home() / ".atlas" / "atlas.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    today = date.today()

    if args.action == "log":
        if args.duration is None:
            print("Error: --duration required")
            print("Usage: atlas-health cardio log --duration 45 --type zone2_cycling")
            conn.close()
            sys.exit(1)

        activity_type = args.type or "zone2_cycling"

        conn.execute("""
            INSERT INTO cardio_log (
                date, activity_type, duration_min, avg_hr, max_hr,
                avg_power_watts, avg_cadence, distance_km, zone_2_minutes, rpe, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            today.isoformat(),
            activity_type,
            args.duration,
            args.hr,
            args.max_hr,
            args.power,
            args.cadence,
            args.distance,
            args.zone2,
            args.rpe,
            args.notes,
        ))
        conn.commit()

        print(f"\u2713 Logged cardio: {activity_type}")
        print(f"  Duration: {args.duration} min")
        if args.hr:
            print(f"  Avg HR: {args.hr} bpm")
        if args.power:
            print(f"  Avg Power: {args.power} W")
        if args.distance:
            print(f"  Distance: {args.distance} km")

    elif args.action == "history":
        days = args.days or 14
        start_date = (today - timedelta(days=days)).isoformat()

        cursor = conn.execute("""
            SELECT date, activity_type, duration_min, avg_hr, avg_power_watts, distance_km, rpe
            FROM cardio_log
            WHERE date >= ?
            ORDER BY date DESC
        """, (start_date,))

        rows = cursor.fetchall()

        print()
        print("=" * 60)
        print(f"  CARDIO LOG - Last {days} days")
        print("=" * 60)

        if not rows:
            print()
            print("  No cardio sessions logged.")
            print("  Log with: atlas-health cardio log --duration 45")
        else:
            print()
            total_minutes = 0
            for row in rows:
                hr_str = f" | HR:{row['avg_hr']}" if row['avg_hr'] else ""
                power_str = f" | {row['avg_power_watts']}W" if row['avg_power_watts'] else ""
                dist_str = f" | {row['distance_km']:.1f}km" if row['distance_km'] else ""
                print(f"  {row['date']}: {row['activity_type']:<16} {row['duration_min']}min{hr_str}{power_str}{dist_str}")
                total_minutes += row['duration_min'] or 0

            print()
            print(f"  Total: {total_minutes} minutes")

        print("=" * 60)

    else:  # show (default) - show weekly summary
        # Get this week's Zone 2 minutes
        week_start = (today - timedelta(days=today.weekday())).isoformat()

        cursor = conn.execute("""
            SELECT SUM(duration_min) as total, SUM(zone_2_minutes) as z2_total, COUNT(*) as sessions
            FROM cardio_log
            WHERE date >= ?
        """, (week_start,))

        row = cursor.fetchone()
        total = row['total'] or 0
        z2 = row['z2_total'] or 0
        sessions = row['sessions'] or 0

        print()
        print("=" * 50)
        print("  CARDIO THIS WEEK")
        print("=" * 50)
        print()
        print(f"  Sessions: {sessions}")
        print(f"  Total minutes: {total}")
        print(f"  Zone 2 minutes: {z2}")
        print(f"  Target: 120 min Zone 2/week")
        print()

        # Progress bar
        progress = min(100, (total / 120) * 100)
        bar_filled = int(progress / 5)
        bar_empty = 20 - bar_filled
        progress_bar = "\u2588" * bar_filled + "\u2591" * bar_empty
        print(f"  [{progress_bar}] {progress:.0f}%")
        print()
        print("=" * 50)

    conn.close()


def cmd_test(args: argparse.Namespace) -> None:
    """Individual test result logging."""
    import sqlite3

    db_path = Path.home() / ".atlas" / "atlas.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    today = date.today()

    # Test name to category mapping
    TEST_CATEGORIES = {
        "wblt_right": ("flexibility", "cm"),
        "wblt_left": ("flexibility", "cm"),
        "sit_reach": ("flexibility", "cm"),
        "shoulder_mobility_right": ("flexibility", "cm"),
        "shoulder_mobility_left": ("flexibility", "cm"),
        "pushups": ("strength", "reps"),
        "pullups": ("strength", "reps"),
        "plank": ("strength", "seconds"),
        "wall_sit": ("strength", "seconds"),
        "dead_hang": ("strength", "seconds"),
        "goblet_squat_1rm": ("strength", "kg"),
        "rdl_1rm": ("strength", "kg"),
        "floor_press_1rm": ("strength", "kg"),
        "sl_balance_eo_right": ("balance", "seconds"),
        "sl_balance_eo_left": ("balance", "seconds"),
        "sl_balance_ec_right": ("balance", "seconds"),
        "sl_balance_ec_left": ("balance", "seconds"),
        "heel_raises_right": ("rehab", "reps"),
        "heel_raises_left": ("rehab", "reps"),
        "zone2_avg_hr": ("cardio", "bpm"),
        "step_test_recovery": ("cardio", "bpm"),
    }

    if args.action == "log":
        if not args.name or args.value is None:
            print("Error: test name and value required")
            print("Usage: atlas-health test log wblt_right 9.5")
            print("       atlas-health test log pushups 25 --pain 0")
            conn.close()
            sys.exit(1)

        test_name = args.name.lower().replace(" ", "_")
        category, unit = TEST_CATEGORIES.get(test_name, ("other", ""))

        conn.execute("""
            INSERT INTO test_results (test_date, test_name, test_category, value, unit, pain_during, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (today.isoformat(), test_name, category, args.value, unit, args.pain, args.notes))
        conn.commit()

        pain_str = f" (pain: {args.pain}/10)" if args.pain else ""
        print(f"\u2713 Logged {test_name}: {args.value} {unit}{pain_str}")

        # Show previous result for comparison
        cursor = conn.execute("""
            SELECT value, test_date FROM test_results
            WHERE test_name = ? AND test_date < ?
            ORDER BY test_date DESC LIMIT 1
        """, (test_name, today.isoformat()))

        prev = cursor.fetchone()
        if prev:
            change = args.value - prev['value']
            direction = "+" if change >= 0 else ""
            print(f"  Previous ({prev['test_date']}): {prev['value']} {unit} ({direction}{change:.1f})")

    elif args.action == "history":
        if not args.name:
            print("Error: test name required")
            print("Usage: atlas-health test history wblt_right")
            conn.close()
            sys.exit(1)

        test_name = args.name.lower().replace(" ", "_")

        cursor = conn.execute("""
            SELECT test_date, value, unit, pain_during, notes
            FROM test_results
            WHERE test_name = ?
            ORDER BY test_date DESC
            LIMIT 20
        """, (test_name,))

        rows = cursor.fetchall()

        print()
        print("=" * 50)
        print(f"  TEST HISTORY: {test_name}")
        print("=" * 50)

        if not rows:
            print()
            print(f"  No history for {test_name}")
        else:
            print()
            for row in rows:
                pain_str = f" (pain:{row['pain_during']})" if row['pain_during'] else ""
                print(f"  {row['test_date']}: {row['value']} {row['unit'] or ''}{pain_str}")

        print("=" * 50)

    else:  # show - list available tests
        print()
        print("=" * 60)
        print("  AVAILABLE TESTS")
        print("=" * 60)
        print()

        categories = {}
        for test, (cat, unit) in TEST_CATEGORIES.items():
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((test, unit))

        for cat, tests in sorted(categories.items()):
            print(f"  {cat.upper()}:")
            for test, unit in tests:
                print(f"    {test:<25} ({unit})")
            print()

        print("  Log: atlas-health test log <name> <value>")
        print("=" * 60)

    conn.close()


def cmd_routine(args: argparse.Namespace) -> None:
    """Daily morning routine commands."""
    routine = load_daily_routine()
    if not routine:
        print("Error: Could not load daily routine configuration.")
        print("Check that config/workouts/phase1.json exists.")
        sys.exit(1)

    if args.action == "show":
        _display_routine(routine)

    elif args.action == "start":
        _interactive_routine(routine)

    elif args.action == "log":
        _log_routine_complete()


def _display_routine(routine: dict) -> None:
    """Display the daily routine in a readable format."""
    name = routine.get("name", "Daily Routine")
    duration = routine.get("duration_minutes", 0)
    sections = routine.get("sections", [])

    print()
    print("=" * 60)
    print(f"  {name} ({duration} min)")
    print("=" * 60)
    print()

    for i, section in enumerate(sections, 1):
        section_name = section.get("name", f"Section {i}")
        section_duration = section.get("duration_minutes", 0)
        exercises = section.get("exercises", [])

        print(f"{i}. {section_name} ({section_duration} min)")
        print("-" * 40)

        for ex in exercises:
            ex_name = ex.get("name", "Unknown")
            sets = ex.get("sets", 1)

            # Format duration/reps
            if "duration_seconds" in ex:
                if sets > 1:
                    time_str = f"{sets}x{ex['duration_seconds']}s"
                else:
                    time_str = f"{ex['duration_seconds']}s"
                if ex.get("per_side"):
                    time_str += "/side"
            elif "duration_minutes" in ex:
                time_str = f"{ex['duration_minutes']} min"
            elif "reps" in ex:
                if sets > 1:
                    time_str = f"{sets}x{ex['reps']} reps"
                else:
                    time_str = f"{ex['reps']} reps"
                if ex.get("per_side"):
                    time_str += "/side"
            else:
                time_str = ""

            print(f"   - {ex_name}: {time_str}")

        print()

    print("=" * 60)
    print("Use 'routine start' for interactive guided routine")
    print("Use 'routine log' to mark complete")
    print()


def _interactive_routine(routine: dict) -> None:
    """Run an interactive guided routine with timers."""
    name = routine.get("name", "Daily Routine")
    sections = routine.get("sections", [])

    print()
    print("=" * 60)
    print(f"  STARTING: {name}")
    print("=" * 60)
    print()
    print("Press Enter to begin, Ctrl+C to cancel...")

    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return

    start_time = time.time()

    for section_idx, section in enumerate(sections, 1):
        section_name = section.get("name", f"Section {section_idx}")
        exercises = section.get("exercises", [])

        print()
        print("=" * 60)
        print(f"  SECTION {section_idx}: {section_name}")
        print("=" * 60)

        for ex_idx, ex in enumerate(exercises, 1):
            ex_name = ex.get("name", "Unknown")
            cues = ex.get("cues", [])

            # Calculate total time for this exercise
            if "duration_seconds" in ex:
                total_seconds = ex["duration_seconds"]
                if ex.get("per_side"):
                    total_seconds *= 2
                if ex.get("sets"):
                    total_seconds *= ex["sets"]
            elif "duration_minutes" in ex:
                total_seconds = ex["duration_minutes"] * 60
            else:
                # For rep-based exercises, estimate 3 seconds per rep
                reps = ex.get("reps", 10)
                if ex.get("per_side"):
                    reps *= 2
                sets = ex.get("sets", 1)
                total_seconds = reps * sets * 3

            print()
            print(f"  [{ex_idx}/{len(exercises)}] {ex_name}")
            print("-" * 40)

            # Show cues
            if cues:
                for cue in cues:
                    print(f"    * {cue}")

            print()

            # Timer or rep counter
            if "duration_seconds" in ex or "duration_minutes" in ex:
                print(f"  Timer: {total_seconds} seconds")
                print("  Press Enter when ready to start timer...")
                try:
                    input()
                except KeyboardInterrupt:
                    print("\nRoutine paused.")
                    return

                # Simple countdown
                for remaining in range(total_seconds, 0, -1):
                    mins, secs = divmod(remaining, 60)
                    if mins > 0:
                        print(f"\r  Time remaining: {mins}:{secs:02d}  ", end="", flush=True)
                    else:
                        print(f"\r  Time remaining: {secs}s    ", end="", flush=True)
                    time.sleep(1)

                print("\r  DONE!                    ")
            else:
                reps = ex.get("reps", 10)
                sets = ex.get("sets", 1)
                per_side = ex.get("per_side", False)

                if sets > 1:
                    print(f"  Perform: {sets} sets x {reps} reps")
                elif per_side:
                    print(f"  Perform: {reps} reps per side")
                else:
                    print(f"  Perform: {reps} reps")

                print("  Press Enter when complete...")
                try:
                    input()
                except KeyboardInterrupt:
                    print("\nRoutine paused.")
                    return

                print("  DONE!")

    elapsed = time.time() - start_time
    elapsed_mins = elapsed / 60

    print()
    print("=" * 60)
    print(f"  ROUTINE COMPLETE!")
    print(f"  Total time: {elapsed_mins:.1f} minutes")
    print("=" * 60)
    print()

    # Offer to log
    print("Log this routine? [Y/n] ", end="")
    try:
        answer = input().strip().lower()
        if answer in ("", "y", "yes"):
            _log_routine_complete()
    except KeyboardInterrupt:
        print("\nNot logged.")


def _log_routine_complete() -> None:
    """Log routine completion to database."""
    import sqlite3

    db_path = Path.home() / ".atlas" / "atlas.db"
    conn = sqlite3.connect(db_path)

    today = date.today()

    # Log as a workout of type 'routine'
    cursor = conn.execute("""
        INSERT INTO workouts (date, type, duration_minutes, notes)
        VALUES (?, 'routine', 18, 'Morning routine completed')
    """, (today.isoformat(),))

    conn.commit()
    workout_id = cursor.lastrowid
    conn.close()

    print(f"Logged morning routine for {today.strftime('%B %d, %Y')} (#{workout_id})")


def cmd_assess(args: argparse.Namespace) -> None:
    """Assessment commands."""
    service = AssessmentService()

    if args.action == "list":
        _display_assessment_list(service, args.category)

    elif args.action == "log":
        if not args.id or args.value is None:
            print("Error: --id and --value required")
            print("Usage: atlas-health assess log --id ankle_dorsiflexion_left --value 9.5")
            sys.exit(1)

        try:
            result_id = service.log_assessment(
                assessment_id=args.id,
                value=args.value,
                notes=args.notes,
            )
            assessment = service.get_assessment_by_id(args.id)
            name = assessment.get("name", args.id) if assessment else args.id
            unit = assessment.get("unit", "") if assessment else ""
            print(f"Logged {name}: {args.value} {unit} (#{result_id})")

            # Show comparison to baseline if exists
            baseline = service.get_baseline(args.id)
            if baseline:
                change = args.value - baseline
                direction = "+" if change >= 0 else ""
                print(f"  Baseline: {baseline} {unit} ({direction}{change:.1f} change)")

        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.action == "progress":
        _display_progress(service, args.category)

    elif args.action == "baseline":
        _display_baseline_protocol(service)

    elif args.action == "gate":
        if not args.gate_number:
            print("Error: gate number required (1-4)")
            print("Usage: atlas-health assess gate 1")
            sys.exit(1)

        _display_gate_evaluation(service, args.gate_number)

    elif args.action == "history":
        if not args.id:
            print("Error: --id required")
            print("Usage: atlas-health assess history --id ankle_dorsiflexion_left")
            sys.exit(1)

        _display_assessment_history(service, args.id)


def _display_assessment_list(service: AssessmentService, category: Optional[str] = None) -> None:
    """Display list of available assessments."""
    tests = service.list_all_tests()

    # Group by category
    by_category = {}
    for test in tests:
        cat = test["category"]
        if category and cat != category:
            continue
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(test)

    if not by_category:
        print(f"No assessments found for category: {category}")
        return

    print()
    print("=" * 70)
    print("  AVAILABLE ASSESSMENTS")
    print("=" * 70)

    for cat, cat_tests in by_category.items():
        print()
        print(f"{cat.upper()}")
        print("-" * 50)
        for test in cat_tests:
            target = f"target: {test['target']}" if test.get("target") else ""
            unit = test.get("unit", "")
            print(f"  {test['id']:<35} {unit:<10} {target}")

    print()
    print("Log an assessment: assess log --id <id> --value <value>")
    print()


def _display_progress(service: AssessmentService, category: Optional[str] = None) -> None:
    """Display progress from baseline."""
    summary = service.get_progress_summary(category)

    if not any(summary.values()):
        print("No assessment data logged yet.")
        print("Run baseline assessments first: assess baseline")
        return

    print()
    print("=" * 70)
    print("  ASSESSMENT PROGRESS")
    print("=" * 70)

    for cat, results in summary.items():
        if not results:
            continue

        print()
        print(f"{cat.upper()}")
        print("-" * 60)

        for r in results:
            status = ""
            if r["meets_target"]:
                status = "TARGET"
            elif r["meets_minimum"]:
                status = "OK"
            else:
                status = "BELOW MIN"

            change_str = ""
            if r["change"] is not None:
                direction = "+" if r["change"] >= 0 else ""
                change_str = f"({direction}{r['change']:.1f})"

            baseline_str = f"baseline: {r['baseline']}" if r["baseline"] else "(first test)"

            print(f"  {r['name'][:30]:<32} {r['value']:>6} {r['unit']:<8} {change_str:<10} [{status}]")

    print()


def _display_baseline_protocol(service: AssessmentService) -> None:
    """Display baseline testing protocol."""
    config = service.config

    print()
    print("=" * 70)
    print(f"  {config['metadata']['name']}")
    print(f"  Duration: ~{config['metadata']['duration_minutes']} minutes")
    print("=" * 70)

    categories = ["strength", "mobility", "stability", "cardio", "calf_strength"]

    for cat in categories:
        assessments = config.get("assessments", {}).get(cat, [])
        if not assessments:
            continue

        print()
        print(f"{cat.upper()}")
        print("-" * 60)

        for a in assessments:
            print(f"\n  {a['name']}")
            print(f"  Protocol: {a.get('protocol', 'See notes')}")
            if a.get("target"):
                print(f"  Target: {a['target']} {a.get('unit', '')}")
            if a.get("notes"):
                print(f"  Note: {a['notes']}")

    # Pain baseline
    print()
    print("PAIN BASELINE")
    print("-" * 60)
    pain_config = config.get("pain_baseline", {})
    print(f"  Scale: {pain_config.get('scale', '0-10')}")
    print(f"  Timing: {pain_config.get('measure_timing', 'Upon waking')}")
    print("  Body parts:")
    for bp in pain_config.get("body_parts", []):
        print(f"    - {bp['name']}: {bp.get('injury', '')}")

    print()
    print("Log results with: assess log --id <test_id> --value <result>")
    print()


def _display_gate_evaluation(service: AssessmentService, gate_number: int) -> None:
    """Display GATE readiness evaluation."""
    try:
        result = service.check_gate(gate_number)
    except ValueError as e:
        print(f"Error: {e}")
        return

    status_emoji = "\u2705" if result.passed else "\u274C"

    print()
    print("=" * 70)
    print(f"  {status_emoji} {result.gate_name}")
    print("=" * 70)

    if result.tests_passed:
        print()
        print("PASSED TESTS:")
        for test in result.tests_passed:
            print(f"  \u2705 {test}")

    if result.tests_failed:
        print()
        print("FAILED TESTS:")
        for test in result.tests_failed:
            print(f"  \u274C {test}")

    if result.lsi_results:
        print()
        print("LIMB SYMMETRY INDEX (LSI):")
        for lsi in result.lsi_results:
            emoji = "\u2705" if lsi.meets_threshold else "\u274C"
            print(f"  {emoji} {lsi.test_name}: {lsi.lsi:.1f}% (L:{lsi.left_value} R:{lsi.right_value})")

    if result.additional_criteria_unmet:
        print()
        print("MANUAL VERIFICATION NEEDED:")
        for criteria in result.additional_criteria_unmet:
            print(f"  [ ] {criteria}")

    print()
    print("-" * 70)
    print(f"Recommendation: {result.recommendation}")
    print()


def _display_assessment_history(service: AssessmentService, assessment_id: str) -> None:
    """Display history for a specific assessment."""
    assessment = service.get_assessment_by_id(assessment_id)
    if not assessment:
        print(f"Unknown assessment: {assessment_id}")
        return

    history = service.get_history(assessment_id)
    if not history:
        print(f"No history for {assessment['name']}")
        return

    unit = assessment.get("unit", "")
    target = assessment.get("target")

    print()
    print("=" * 50)
    print(f"  {assessment['name']} History")
    print("=" * 50)

    for h in history:
        baseline_mark = " (BASELINE)" if h.get("is_baseline") else ""
        date_str = h["date"]
        value = h["value"]
        # Avoid division by zero - check target exists and is non-zero
        if target and target != 0 and value is not None:
            target_pct = f"({(value/target*100):.0f}% of target)"
        else:
            target_pct = ""
        print(f"  {date_str}: {value} {unit} {target_pct}{baseline_mark}")

    print()


def cmd_phase(args: argparse.Namespace) -> None:
    """Phase management commands."""
    service = PhaseService()

    if args.action == "show":
        _display_current_phase(service)

    elif args.action == "check":
        _display_phase_check(service)

    elif args.action == "advance":
        _advance_phase(service, args.force)

    elif args.action == "start":
        _start_phase(service)

    elif args.action == "history":
        _display_phase_history(service)

    elif args.action == "regress":
        _regress_phase(service, args.reason)


def _display_current_phase(service: PhaseService) -> None:
    """Display current phase status."""
    status = service.get_current_phase()

    if not status:
        print()
        print("No active training phase.")
        print("Start Phase 1 with: phase start")
        print()
        return

    phase = status.phase

    # Calculate progress bar
    progress_pct = min(100, (status.weeks_completed / phase.weeks_min) * 100)
    bar_filled = int(progress_pct / 5)
    bar_empty = 20 - bar_filled
    progress_bar = "\u2588" * bar_filled + "\u2591" * bar_empty

    print()
    print("=" * 60)
    print(f"  PHASE {phase.id}: {phase.display_name.upper()}")
    print("=" * 60)
    print()
    print(f"  Focus: {phase.focus}")
    print(f"  Intensity: {phase.intensity_range}")
    print(f"  Volume: {phase.volume_description}")
    print()
    print("-" * 60)
    print(f"  Started: {status.start_date.strftime('%B %d, %Y')}")
    print(f"  Duration: {status.days_in_phase} days ({status.weeks_completed} weeks)")
    print(f"  Progress: [{progress_bar}] {progress_pct:.0f}%")
    print(f"  Minimum: {phase.weeks_min} weeks | Maximum: {phase.weeks_max or 'N/A'} weeks")
    print()
    print("-" * 60)
    print("  METRICS THIS PHASE:")
    print(f"    RED days this week: {status.red_days_this_week}")
    print(f"    RED days avg/week:  {status.red_days_avg:.1f}")
    print(f"    Max pain (7 days):  {status.max_pain_level}/10")
    print()

    # Show GATE requirement if applicable
    if status.gate_required:
        print("-" * 60)
        gate_emoji = "\u2705" if status.gate_passed else "\u274C"
        print(f"  GATE {status.gate_required} REQUIREMENT: {gate_emoji} {'PASSED' if status.gate_passed else 'NOT PASSED'}")
        if status.gate_details and not status.gate_passed:
            failed = status.gate_details.get("tests_failed", [])
            if failed:
                print(f"    Failed tests: {len(failed)}")
                for test in failed[:3]:  # Show first 3
                    print(f"      - {test}")
                if len(failed) > 3:
                    print(f"      ... and {len(failed) - 3} more")
            print(f"    Run 'assess gate {status.gate_required}' for full details")
        print()

    # Show advancement status
    if status.can_advance:
        print("  \u2705 READY TO ADVANCE")
    else:
        print("  \u23F3 NOT YET READY TO ADVANCE")

    if status.advancement_met:
        print()
        print("  Met:")
        for item in status.advancement_met:
            print(f"    \u2705 {item}")

    if status.advancement_blockers:
        print()
        print("  Blockers:")
        for item in status.advancement_blockers:
            print(f"    \u274C {item}")

    # Check regression triggers
    triggers = service.check_regression_triggers()
    if triggers:
        print()
        print("  \u26A0\uFE0F  REGRESSION TRIGGERS DETECTED:")
        for trigger in triggers:
            print(f"    - {trigger}")

    print()
    print("=" * 60)
    print("  Commands: phase check | phase advance | phase history")
    print()


def _display_phase_check(service: PhaseService) -> None:
    """Display detailed progression check."""
    status = service.get_current_phase()

    if not status:
        print("No active phase. Start with: phase start")
        return

    phase = status.phase
    check = service.check_progression(
        phase,
        status.weeks_completed,
        status.red_days_avg,
        status.max_pain_level,
    )

    status_emoji = "\u2705" if check.ready else "\u274C"

    print()
    print("=" * 60)
    print(f"  {status_emoji} PROGRESSION CHECK: {phase.display_name} -> Next Phase")
    print("=" * 60)

    if check.criteria_met:
        print()
        print("  CRITERIA MET:")
        for item in check.criteria_met:
            print(f"    \u2705 {item}")

    if check.criteria_not_met:
        print()
        print("  CRITERIA NOT MET:")
        for item in check.criteria_not_met:
            print(f"    \u274C {item}")

    if check.warnings:
        print()
        print("  WARNINGS:")
        for item in check.warnings:
            print(f"    \u26A0\uFE0F  {item}")

    print()
    print("-" * 60)
    print(f"  Recommendation: {check.recommendation}")
    print()

    if check.ready:
        print("  To advance: phase advance")
    print()


def _advance_phase(service: PhaseService, force: bool = False) -> None:
    """Advance to next phase."""
    if force:
        print("Forcing phase advancement...")

    success, message = service.advance_phase(force=force)

    if success:
        print(f"\u2705 {message}")
        print()
        # Show new phase status
        _display_current_phase(service)
    else:
        print(f"\u274C {message}")
        print()
        print("Use 'phase check' for details, or 'phase advance --force' to override.")


def _start_phase(service: PhaseService) -> None:
    """Start Phase 1."""
    current = service.get_current_phase()

    if current:
        print(f"Already in {current.phase.display_name}.")
        print("Use 'phase advance' to move to next phase.")
        return

    service.start_phase("phase_1")
    print("\u2705 Started Phase 1: Foundation")
    print()
    _display_current_phase(service)


def _regress_phase(service: PhaseService, reason: Optional[str] = None) -> None:
    """Regress to previous phase."""
    reason = reason or "manual regression"
    success, message = service.regress_phase(reason)

    if success:
        print(f"\u2705 {message}")
        print(f"   Reason: {reason}")
        print()
        _display_current_phase(service)
    else:
        print(f"\u274C {message}")


def _display_phase_history(service: PhaseService) -> None:
    """Display phase transition history."""
    history = service.get_phase_history()

    if not history:
        print("No phase history yet.")
        print("Start with: phase start")
        return

    print()
    print("=" * 60)
    print("  PHASE HISTORY")
    print("=" * 60)

    for entry in history:
        status_emoji = {
            "active": "\u25B6\uFE0F ",
            "completed": "\u2705",
            "regressed": "\u26A0\uFE0F ",
        }.get(entry["status"], "")

        start = entry["start_date"]
        end = entry["end_date"] or "present"
        phase_name = entry["display_name"]
        exit_reason = entry["exit_reason"] or ""

        print()
        print(f"  {status_emoji} {phase_name}")
        print(f"     {start} -> {end}")
        if exit_reason:
            print(f"     Exit: {exit_reason}")
        if entry["notes"]:
            print(f"     Notes: {entry['notes']}")

    print()


def cmd_stats(args: argparse.Namespace) -> None:
    """Health statistics."""
    workout_service = WorkoutService()
    supplement_service = SupplementService()

    print()
    if args.week:
        print("=" * 60)
        print(f"  WEEKLY STATS - {date.today().strftime('%B %d, %Y')}")
        print("=" * 60)

        # Workout stats
        workout_stats = workout_service.get_weekly_stats()
        completed = workout_stats["completed"]
        expected = workout_stats["expected"]
        pct = workout_stats["completion_pct"]
        duration = workout_stats["total_duration_minutes"]

        print()
        print("WORKOUTS:")
        print(f"  Completed: {completed}/{expected} ({pct:.0f}%)")
        print(f"  Total time: {duration} minutes")
        if workout_stats["by_type"]:
            by_type = ", ".join(f"{k}:{v}" for k, v in workout_stats["by_type"].items())
            print(f"  By type: {by_type}")

        # Supplement stats
        supp_stats = supplement_service.get_weekly_compliance()
        taken = supp_stats["total_taken"]
        possible = supp_stats["total_possible"]
        compliance = supp_stats["compliance_pct"]

        print()
        print("SUPPLEMENTS:")
        print(f"  Compliance: {compliance:.0f}% ({taken}/{possible} doses)")

        # Per supplement
        print("  By supplement:")
        for name, count in supp_stats["by_supplement"].items():
            print(f"    {name}: {count}/7 days")

        print("=" * 60)

    else:
        # Daily stats (default)
        checklist = supplement_service.get_today()
        plan = workout_service.get_todays_workout()

        print("DAILY STATUS:")
        print(f"  Supplements: {checklist.taken_count}/{checklist.total} ({checklist.completion_pct:.0f}%)")
        if plan:
            print(f"  Scheduled: {plan.protocol.name}")


def cmd_garmin(args: argparse.Namespace) -> None:
    """Garmin Connect integration commands."""
    import asyncio
    from atlas.health.garmin import GarminService, is_garmin_auth_valid, print_setup_instructions

    service = GarminService()

    if args.action == "status":
        configured = service.is_configured()
        valid = service.has_valid_token()

        print()
        print("=" * 50)
        print("  GARMIN CONNECT STATUS")
        print("=" * 50)
        print()
        print(f"  Configured:     {'Yes' if configured else 'No'}")
        print(f"  Session valid:  {'Yes' if valid else 'No'}")
        print()

        if not configured:
            print("  To configure:")
            print("    1. Add GARMIN_USERNAME and GARMIN_PASSWORD to .env")
            print("    2. Run: python scripts/garmin_auth_setup.py")
            print("    3. Remove GARMIN_PASSWORD from .env after success")
        elif not valid:
            print("  Session expired. Re-run: python scripts/garmin_auth_setup.py")
        else:
            print("  Ready to sync! Run: atlas-health garmin sync")
        print()
        print("=" * 50)

    elif args.action == "sync":
        if not service.is_configured():
            print("Not configured. Run: python scripts/garmin_auth_setup.py")
            sys.exit(1)

        if not is_garmin_auth_valid():
            print("Session expired. Run: python scripts/garmin_auth_setup.py")
            sys.exit(1)

        print("Syncing Garmin data...")
        result = asyncio.run(service.sync_today())

        if result:
            print()
            print("=" * 50)
            print("  GARMIN SYNC RESULTS")
            print("=" * 50)
            print()
            print(f"  Status:       {result.sync_status}")
            print()
            print("  SLEEP:")
            print(f"    Hours:      {result.sleep_hours or 'N/A'}")
            print(f"    Score:      {result.sleep_score or 'N/A'}")
            if result.deep_sleep_minutes:
                print(f"    Deep:       {result.deep_sleep_minutes} min")
            if result.rem_sleep_minutes:
                print(f"    REM:        {result.rem_sleep_minutes} min")
            print()
            print("  HEART:")
            print(f"    RHR:        {result.resting_hr or 'N/A'} bpm")
            print(f"    HRV Status: {result.hrv_status or 'N/A'}")
            print(f"    HRV Avg:    {result.hrv_avg or 'N/A'}")
            print()
            print("  RECOVERY:")
            print(f"    Body Battery: {result.body_battery or 'N/A'}%")
            print(f"    Stress Avg:   {result.stress_avg or 'N/A'}")
            print()

            if result.missing_fields:
                print(f"  Missing: {', '.join(result.missing_fields)}")
                print()

            print("=" * 50)
        else:
            print("Sync failed. Check logs for details.")
            sys.exit(1)

    elif args.action == "setup":
        print_setup_instructions()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ATLAS Health Tracking CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s daily --sleep 7.2 --hrv BALANCED
    %(prog)s workout
    %(prog)s workout log --duration 45 --type strength
    %(prog)s supplements
    %(prog)s supplements check "Vitamin D"
    %(prog)s supplements add "Creatine" --dosage "5g" --timing morning
    %(prog)s stats --week
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # atlas-health daily
    daily = subparsers.add_parser("daily", help="Morning sync and daily status")

    def validate_sleep_hours(value):
        fvalue = float(value)
        if fvalue < 0 or fvalue > 24:
            raise argparse.ArgumentTypeError(f"Sleep hours must be between 0 and 24, got {value}")
        return fvalue

    daily.add_argument("--sleep", type=validate_sleep_hours, help="Sleep hours (e.g., 7.2)")
    daily.add_argument(
        "--hrv",
        type=str,
        choices=["BALANCED", "UNBALANCED", "LOW", "HIGH", "STRAINED", "GOOD", "EXCELLENT"],
        help="HRV status",
    )
    daily.add_argument("--rhr", type=int, help="Resting heart rate in bpm")
    daily.add_argument("--no-sync", action="store_true", help="Skip Garmin sync (future)")

    # atlas-health workout
    workout = subparsers.add_parser("workout", help="Workout management")
    workout.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "log", "history"],
        help="Action to perform",
    )
    workout.add_argument("--duration", type=int, help="Workout duration in minutes")
    workout.add_argument("--type", choices=["strength", "cardio", "mobility", "recovery"])
    workout.add_argument("--energy-before", type=int, choices=range(1, 11), metavar="1-10")
    workout.add_argument("--energy-after", type=int, choices=range(1, 11), metavar="1-10")
    workout.add_argument("--notes", type=str, help="Workout notes")
    workout.add_argument("--days", type=int, default=14, help="Days of history to show")
    workout.add_argument("--red", action="store_true", help="Show RED day workout")
    workout.add_argument("--yellow", action="store_true", help="Show YELLOW day workout")

    # atlas-health supplements
    supps = subparsers.add_parser("supplements", help="Supplement tracking")
    supps.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "check", "all-morning", "all-evening", "add", "list"],
        help="Action to perform",
    )
    supps.add_argument("name", nargs="?", help="Supplement name")
    supps.add_argument("--dosage", help="Dosage (e.g., '5000 IU', '500mg')")
    supps.add_argument("--timing", choices=["morning", "with_meal", "before_bed"])
    supps.add_argument("--purpose", help="Why taking this supplement")
    supps.add_argument("--brand", help="Brand name")

    # atlas-health stats
    stats = subparsers.add_parser("stats", help="Health statistics")
    stats.add_argument("--week", action="store_true", help="Weekly stats")
    stats.add_argument("--month", action="store_true", help="Monthly stats")

    # atlas-health pain
    pain = subparsers.add_parser("pain", help="Pain tracking")
    pain.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "log", "all"],
        help="Action: show today's pain, log single, or log all",
    )
    pain.add_argument("body_part", nargs="?", help="Body part (shoulder_right, ankle_left, etc.)")
    pain.add_argument("--level", type=int, choices=range(0, 11), metavar="0-10", help="Pain level")
    pain.add_argument("--notes", help="Notes")

    # atlas-health weight
    weight = subparsers.add_parser("weight", help="Weight tracking")
    weight.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "log", "trend"],
        help="Action: show recent, log new, or show trend",
    )
    weight.add_argument("weight", nargs="?", type=float, help="Weight in kg (e.g., 82.3)")
    weight.add_argument("--bf", type=float, help="Body fat percentage (e.g., 18.5)")
    weight.add_argument("--days", type=int, default=7, help="Days for trend (default: 7)")
    weight.add_argument("--notes", help="Notes")

    # atlas-health routine
    routine = subparsers.add_parser("routine", help="Daily morning routine")
    routine.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "start", "log"],
        help="Action: show routine, start interactive, or log completion",
    )

    # atlas-health assess
    assess = subparsers.add_parser("assess", help="Fitness assessments and GATE checks")
    assess.add_argument(
        "action",
        nargs="?",
        default="list",
        choices=["list", "log", "progress", "baseline", "gate", "history"],
        help="Action: list tests, log result, show progress, baseline protocol, check GATE, or history",
    )
    assess.add_argument("gate_number", nargs="?", type=int, help="GATE number (1-4) for gate action")
    assess.add_argument("--id", help="Assessment ID to log or view")
    assess.add_argument("--value", type=float, help="Assessment value to log")
    assess.add_argument("--category", help="Filter by category (strength, mobility, stability, cardio)")
    assess.add_argument("--notes", help="Notes for assessment")

    # atlas-health phase
    phase = subparsers.add_parser("phase", help="Training phase management")
    phase.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "check", "advance", "start", "history", "regress"],
        help="Action: show current, check readiness, advance, start phase 1, history, or regress",
    )
    phase.add_argument("--force", action="store_true", help="Force advancement even if not ready")
    phase.add_argument("--reason", help="Reason for regression")

    # atlas-health garmin
    garmin = subparsers.add_parser("garmin", help="Garmin Connect integration")
    garmin.add_argument(
        "action",
        nargs="?",
        default="status",
        choices=["status", "sync", "setup"],
        help="Action: check status, sync data, or show setup instructions",
    )

    # atlas-health cardio
    cardio = subparsers.add_parser("cardio", help="Cardio session logging")
    cardio.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "log", "history"],
        help="Action: show weekly summary, log session, or show history",
    )
    cardio.add_argument("--duration", type=int, help="Duration in minutes")
    cardio.add_argument("--type", default="zone2_cycling",
                        choices=["zone2_cycling", "zone2_walk", "family_hike", "vo2max_intervals"],
                        help="Activity type")
    cardio.add_argument("--hr", type=int, help="Average heart rate")
    cardio.add_argument("--max-hr", type=int, help="Max heart rate")
    cardio.add_argument("--power", type=int, help="Average power in watts")
    cardio.add_argument("--cadence", type=int, help="Average cadence")
    cardio.add_argument("--distance", type=float, help="Distance in km")
    cardio.add_argument("--zone2", type=int, help="Minutes in Zone 2")
    cardio.add_argument("--rpe", type=int, choices=range(1, 11), metavar="1-10", help="RPE")
    cardio.add_argument("--days", type=int, default=14, help="Days of history")
    cardio.add_argument("--notes", help="Notes")

    # atlas-health test
    test = subparsers.add_parser("test", help="Individual test result logging")
    test.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "log", "history"],
        help="Action: show available tests, log result, or show history",
    )
    test.add_argument("name", nargs="?", help="Test name (e.g., wblt_right, pushups)")
    test.add_argument("value", nargs="?", type=float, help="Test value")
    test.add_argument("--pain", type=int, choices=range(0, 11), metavar="0-10", help="Pain during test")
    test.add_argument("--notes", help="Notes")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Route to command handlers
    handlers = {
        "daily": cmd_daily,
        "workout": cmd_workout,
        "supplements": cmd_supplements,
        "stats": cmd_stats,
        "pain": cmd_pain,
        "weight": cmd_weight,
        "routine": cmd_routine,
        "assess": cmd_assess,
        "phase": cmd_phase,
        "garmin": cmd_garmin,
        "cardio": cmd_cardio,
        "test": cmd_test,
    }

    if args.command in handlers:
        try:
            handlers[args.command](args)
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
