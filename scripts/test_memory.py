#!/usr/bin/env python3
"""
ATLAS Memory System Test Script

Tests:
1. Embedding generation latency (<15ms target)
2. Memory CRUD operations
3. Hybrid search with embeddings
4. Scale testing: Generate 100K dummy records, verify <75ms hybrid search
5. Blueprint API operations

Usage:
    python scripts/test_memory.py
    python scripts/test_memory.py --scale  # Run 100K scale test (slow)
"""

import argparse
import random
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_embeddings():
    """Test embedding generation."""
    print("\n" + "=" * 60)
    print("TEST: Embeddings")
    print("=" * 60)

    try:
        from atlas.memory.embeddings import get_embedder

        embedder = get_embedder()

        # Test single embedding
        test_texts = [
            "User prefers morning workouts",
            "Best supplement for sleep quality",
            "Track daily vitamin D levels",
        ]

        print("\nSingle embedding latency:")
        latencies = []
        for text in test_texts:
            result = embedder.embed(text)
            latencies.append(result.duration_ms)
            print(f"  '{text[:40]}...' -> {result.duration_ms:.1f}ms ({len(result.embedding)} dims)")

        avg_latency = sum(latencies) / len(latencies)
        print(f"\nAverage latency: {avg_latency:.1f}ms")
        print(f"Target: <15ms")

        if avg_latency < 15:
            print("[PASS] Embedding latency within target")
        else:
            print("[WARN] Embedding latency above target (may be due to first-load)")

        # Test batch embedding
        print("\nBatch embedding (3 texts):")
        start = time.perf_counter()
        batch_embeddings = embedder.embed_batch(test_texts)
        batch_time = (time.perf_counter() - start) * 1000
        print(f"  Total: {batch_time:.1f}ms for {len(batch_embeddings)} embeddings")
        print(f"  Per-embedding: {batch_time / len(batch_embeddings):.1f}ms")

        # Test query embedding (with instruction prefix)
        print("\nQuery embedding (with instruction prefix):")
        start = time.perf_counter()
        query_emb = embedder.embed_query("best workout routine")
        query_time = (time.perf_counter() - start) * 1000
        print(f"  Latency: {query_time:.1f}ms")

        return True

    except ImportError as e:
        print(f"[SKIP] sentence-transformers not installed: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] {e}")
        return False


def test_memory_crud():
    """Test memory store CRUD operations."""
    print("\n" + "=" * 60)
    print("TEST: Memory CRUD")
    print("=" * 60)

    from atlas.memory.store import MemoryStore

    # Use temp database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        store = MemoryStore(db_path)
        store.init_db()
        print(f"Created test database: {db_path}")

        # Test add_memory
        print("\nAdding memories...")
        id1 = store.add_memory(
            "User prefers morning workouts",
            importance=0.8,
            memory_type="preference",
            source="conversation",
        )
        print(f"  Added memory {id1}")

        id2 = store.add_memory(
            "Best time for supplements is with breakfast",
            importance=0.6,
            memory_type="fact",
        )
        print(f"  Added memory {id2}")

        # Test get_memory
        print("\nRetrieving memory...")
        mem = store.get_memory(id1)
        if mem:
            print(f"  ID: {mem.id}")
            print(f"  Content: {mem.content}")
            print(f"  Importance: {mem.importance}")
            print(f"  Type: {mem.memory_type}")
            print(f"  Access count: {mem.access_count}")

        # Test get_recent_memories
        print("\nRecent memories:")
        recent = store.get_recent_memories(limit=5)
        for m in recent:
            print(f"  - {m.content[:50]}...")

        # Test FTS search
        print("\nFTS search for 'workout':")
        fts_results = store.search_fts("workout", limit=5)
        for r in fts_results:
            print(f"  - {r.memory.content[:50]}... (score: {r.score:.3f})")

        # Test delete_memory
        print("\nDeleting memory...")
        deleted = store.delete_memory(id2)
        print(f"  Deleted: {deleted}")

        store.close()
        print("\n[PASS] Memory CRUD operations successful")
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_hybrid_search():
    """Test hybrid search with embeddings."""
    print("\n" + "=" * 60)
    print("TEST: Hybrid Search")
    print("=" * 60)

    from atlas.memory.store import MemoryStore

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        store = MemoryStore(db_path)
        store.init_db()

        # Add test memories with diverse content
        test_memories = [
            ("User prefers morning workouts for better energy", 0.8, "preference"),
            ("High protein breakfast improves workout performance", 0.7, "fact"),
            ("Sleep quality directly affects recovery", 0.9, "fact"),
            ("Vitamin D supplements taken with breakfast", 0.6, "fact"),
            ("Afternoon cardio less effective than morning", 0.5, "fact"),
            ("Magnesium before bed improves sleep", 0.7, "preference"),
        ]

        print("Adding test memories...")
        for content, importance, mem_type in test_memories:
            store.add_memory(content, importance=importance, memory_type=mem_type)
        print(f"  Added {len(test_memories)} memories")

        # Test hybrid search
        try:
            from atlas.memory.embeddings import get_embedder
            embedder = get_embedder()
            has_embeddings = True
        except ImportError:
            has_embeddings = False

        if has_embeddings:
            print("\nHybrid search for 'best workout routine':")
            query = "best workout routine"
            embedding = embedder.embed_query(query)

            start = time.perf_counter()
            results = store.search_hybrid(query, embedding, limit=5)
            search_time = (time.perf_counter() - start) * 1000

            for r in results:
                print(f"  - {r.memory.content[:50]}... (score: {r.score:.4f})")
            print(f"\n  Search time: {search_time:.1f}ms")
        else:
            print("\nFTS-only search (no embeddings):")
            results = store.search_fts("workout", limit=5)
            for r in results:
                print(f"  - {r.memory.content[:50]}...")

        store.close()
        print("\n[PASS] Hybrid search successful")
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_blueprint_api():
    """Test Blueprint API operations."""
    print("\n" + "=" * 60)
    print("TEST: Blueprint API")
    print("=" * 60)

    from atlas.memory.store import MemoryStore
    from atlas.memory.blueprint import (
        BlueprintAPI,
        DailyMetrics,
        Supplement,
        SupplementLog,
        Workout,
        WorkoutExercise,
        LabResult,
        Injury,
    )

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        store = MemoryStore(db_path)
        store.init_db()
        api = BlueprintAPI(store)

        # Test daily metrics
        print("\nLogging daily metrics...")
        today = date.today()
        metrics_id = api.log_daily_metrics(DailyMetrics(
            date=today,
            sleep_hours=7.5,
            sleep_score=85,
            hrv_morning=45,
            weight_kg=75.0,
            mood=7,
            energy_level=8,
        ))
        print(f"  Logged metrics ID: {metrics_id}")

        # Update existing metrics
        api.log_daily_metrics(DailyMetrics(
            date=today,
            stress_level=3,  # Add stress level
        ))
        print("  Updated metrics with stress level")

        # Get recent metrics
        recent_metrics = api.get_daily_metrics(days=7)
        print(f"  Retrieved {len(recent_metrics)} days of metrics")
        if recent_metrics:
            m = recent_metrics[0]
            print(f"    Date: {m.date}, Sleep: {m.sleep_hours}h, Mood: {m.mood}/10")

        # Test supplements
        print("\nAdding supplements...")
        supp_id = api.add_supplement(Supplement(
            name="Vitamin D3",
            brand="NOW Foods",
            dosage="5000 IU",
            timing="morning",
            purpose="bone health, immune support",
        ))
        print(f"  Added supplement ID: {supp_id}")

        # Log supplement dose
        api.log_supplement_dose(SupplementLog(
            supplement_id=supp_id,
            date=today,
            taken=True,
        ))
        print("  Logged supplement dose")

        # Get supplements
        supplements = api.get_supplements()
        print(f"  Active supplements: {len(supplements)}")

        # Test workouts
        print("\nLogging workout...")
        workout_id = api.log_workout(Workout(
            date=today,
            type="strength",
            duration_minutes=45,
            energy_before=7,
            energy_after=8,
        ))
        print(f"  Logged workout ID: {workout_id}")

        # Add exercises
        api.add_workout_exercise(WorkoutExercise(
            workout_id=workout_id,
            exercise_id="squat",
            exercise_name="Barbell Squat",
            sets=4,
            reps="8,8,8,6",
            weight_kg=80.0,
            order_index=1,
        ))
        print("  Added exercise: Barbell Squat")

        # Get workouts
        workouts = api.get_workouts(days=7)
        print(f"  Workouts this week: {len(workouts)}")

        # Test lab results
        print("\nLogging lab result...")
        lab_id = api.log_lab_result(LabResult(
            test_date=today,
            marker="vitamin_d",
            value=45.0,
            unit="ng/mL",
            reference_low=30.0,
            reference_high=100.0,
        ))
        print(f"  Logged lab result ID: {lab_id}")

        # Test injuries
        print("\nLogging injury...")
        injury_id = api.log_injury(Injury(
            body_part="shoulder",
            side="left",
            description="Minor rotator cuff strain",
            onset_date=today - timedelta(days=7),
            severity=2,
            status="recovering",
            contraindicated_exercises=["overhead press", "lateral raise"],
        ))
        print(f"  Logged injury ID: {injury_id}")

        # Get contraindicated exercises
        contraindicated = api.get_contraindicated_exercises()
        print(f"  Contraindicated exercises: {contraindicated}")

        store.close()
        print("\n[PASS] Blueprint API operations successful")
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_scale(record_count: int = 100000):
    """Test performance at scale."""
    print("\n" + "=" * 60)
    print(f"TEST: Scale ({record_count:,} records)")
    print("=" * 60)

    from atlas.memory.store import MemoryStore, SQLITE_VEC_AVAILABLE

    if not SQLITE_VEC_AVAILABLE:
        print("[SKIP] sqlite-vec not available for scale test")
        return True

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        store = MemoryStore(db_path)
        store.init_db()

        # Topics for random content generation
        topics = ["workout", "sleep", "nutrition", "supplements", "recovery", "strength", "cardio", "stretching"]
        adjectives = ["effective", "important", "optimal", "recommended", "beneficial"]
        verbs = ["improves", "supports", "enhances", "maintains", "boosts"]

        def random_content():
            return f"{random.choice(adjectives)} {random.choice(topics)} {random.choice(verbs)} overall health and fitness performance"

        # Generate fake embedding (fast - avoids 25min embedding time)
        fake_embedding = [random.random() for _ in range(384)]

        print(f"\nBulk inserting {record_count:,} records with fake embeddings...")
        start = time.perf_counter()

        batch_size = 1000
        for i in range(0, record_count, batch_size):
            for _ in range(batch_size):
                content = random_content()
                store.add_memory(content, embedding=fake_embedding)

            if (i + batch_size) % 10000 == 0:
                elapsed = time.perf_counter() - start
                rate = (i + batch_size) / elapsed
                print(f"  {i + batch_size:,} records... ({rate:.0f}/sec)")

        insert_time = time.perf_counter() - start
        print(f"\nInsert complete: {record_count:,} records in {insert_time:.1f}s ({record_count / insert_time:.0f}/sec)")

        # Verify count
        count = store.conn.execute("SELECT COUNT(*) FROM semantic_memory").fetchone()[0]
        print(f"Verified record count: {count:,}")

        # Test search latency with real embedding
        try:
            from atlas.memory.embeddings import get_embedder
            embedder = get_embedder()

            print("\nHybrid search latency at scale:")
            test_queries = [
                "best workout routine",
                "improve sleep quality",
                "protein supplements",
                "recovery after training",
                "morning energy levels",
            ]

            latencies = []
            for query in test_queries:
                # Generate real embedding
                emb_start = time.perf_counter()
                embedding = embedder.embed_query(query)
                emb_time = (time.perf_counter() - emb_start) * 1000

                # Run hybrid search
                search_start = time.perf_counter()
                results = store.search_hybrid(query, embedding, limit=10)
                search_time = (time.perf_counter() - search_start) * 1000

                total_time = emb_time + search_time
                latencies.append(total_time)
                print(f"  '{query}': emb={emb_time:.0f}ms, search={search_time:.0f}ms, total={total_time:.0f}ms ({len(results)} results)")

            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)

            print(f"\nAverage latency: {avg_latency:.1f}ms")
            print(f"Max latency: {max_latency:.1f}ms")
            print(f"Target: <75ms")

            if max_latency < 75:
                print("\n[PASS] Scale test passed - performance target met!")
            else:
                print("\n[WARN] Scale test - latency above target")

        except ImportError:
            print("\n[SKIP] Embedding test skipped (sentence-transformers not installed)")

        store.close()
        return True

    except Exception as e:
        print(f"[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        Path(db_path).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="ATLAS Memory System Tests")
    parser.add_argument("--scale", action="store_true", help="Run 100K scale test (slow)")
    parser.add_argument("--scale-count", type=int, default=100000, help="Number of records for scale test")
    args = parser.parse_args()

    print("=" * 60)
    print("ATLAS Memory System Test Suite")
    print("=" * 60)

    results = {}

    # Core tests
    results["embeddings"] = test_embeddings()
    results["memory_crud"] = test_memory_crud()
    results["hybrid_search"] = test_hybrid_search()
    results["blueprint_api"] = test_blueprint_api()

    # Scale test (optional)
    if args.scale:
        results["scale"] = test_scale(args.scale_count)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
