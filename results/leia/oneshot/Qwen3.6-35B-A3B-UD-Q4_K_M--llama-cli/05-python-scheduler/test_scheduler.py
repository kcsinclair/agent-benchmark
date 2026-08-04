"""Verify scheduler.py correctness on all example + edge cases."""
import time
from scheduler import best_schedule

def test_example():
    jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
    total, indices = best_schedule(jobs)
    print(f"Example: weight={total}, indices={indices}")
    assert total == 13.0, f"Expected 13.0, got {total}"
    # Verify the subset is valid (non-overlapping)
    chosen = [jobs[i] for i in indices]
    chosen.sort(key=lambda x: x[0])
    for i in range(len(chosen) - 1):
        assert chosen[i][1] <= chosen[i+1][0], f"Jobs {chosen[i]} and {chosen[i+1]} overlap"
    # Verify total weight
    assert sum(c[2] for c in chosen) == 13.0
    print("✓ example passed")

def test_empty():
    total, indices = best_schedule([])
    assert total == 0.0 and indices == []
    print("✓ empty passed")

def test_single():
    jobs = [(1, 5, 10)]
    total, indices = best_schedule(jobs)
    assert total == 10.0 and indices == [0]
    print("✓ single passed")

def test_touching_allowed():
    jobs = [(0, 5, 3), (5, 10, 4)]
    total, indices = best_schedule(jobs)
    assert total == 7.0, f"Expected 7.0, got {total}"
    assert sorted(indices) == [0, 1]
    print("✓ touching passed")

def test_all_overlap():
    jobs = [(0, 10, 1), (2, 8, 5), (4, 6, 3)]
    total, indices = best_schedule(jobs)
    assert total == 5.0 and indices == [1]
    print("✓ all overlap passed")

def test_no_overlap():
    jobs = [(0, 2, 1), (2, 4, 2), (4, 6, 3), (6, 8, 4), (8, 10, 5)]
    total, indices = best_schedule(jobs)
    assert total == 15.0, f"Expected 15.0, got {total}"
    assert len(indices) == 5
    print("✓ no overlap passed")

def test_performance():
    import random
    random.seed(42)
    n = 200_000
    # Generate non-trivial test: random jobs in [0, 100000]
    jobs = []
    for _ in range(n):
        s = random.randint(0, 90000)
        length = random.randint(1, 9999)
        e = min(s + length, 100000)
        w = random.randint(1, 100)
        jobs.append((float(s), float(e), float(w)))
    t0 = time.perf_counter()
    total, indices = best_schedule(jobs)
    elapsed = time.perf_counter() - t0
    print(f"✓ performance: n={n}, weight={total:.2f}, time={elapsed:.3f}s")
    assert elapsed < 10, f"Took {elapsed:.3f}s, expected < 10s"
    # Verify subset validity
    chosen = [jobs[i] for i in indices]
    chosen.sort(key=lambda x: x[0])
    for i in range(len(chosen) - 1):
        assert chosen[i][1] <= chosen[i+1][0], f"Jobs overlap at {chosen[i]} and {chosen[i+1]}"
    assert sum(c[2] for c in chosen) == total
    print(f"  subset size={len(indices)}, valid non-overlapping")

test_example()
test_empty()
test_single()
test_touching_allowed()
test_all_overlap()
test_no_overlap()
test_performance()
print("\nAll tests passed.")
