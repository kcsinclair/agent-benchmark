from scheduler import best_schedule

# Example from the problem
jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
weight, idx = best_schedule(jobs)
print(f"weight={weight}, indices={idx}")
assert abs(weight - 13.0) < 1e-12, f"Expected weight 13.0, got {weight}"
# Validate non-overlapping and correctness
chosen = [jobs[i] for i in idx]
for a in range(len(chosen)):
    for b in range(a + 1, len(chosen)):
        s1, e1, _ = chosen[a]
        s2, e2, _ = chosen[b]
        # No overlap: one starts at or after the other ends
        assert s2 >= e1 or s1 >= e2, f"Overlapping jobs: {chosen[a]} and {chosen[b]}"
# Check sorted by start time, ties by index ascending
for i in range(len(idx) - 1):
    if jobs[idx[i]][0] == jobs[idx[i + 1]][0]:
        assert idx[i] < idx[i + 1], f"Tie not broken by index ascending: {idx[i]} vs {idx[i+1]}"
    else:
        assert jobs[idx[i]][0] < jobs[idx[i + 1]][0], f"Not sorted by start time: {idx[i]} vs {idx[i+1]}"

# Empty case
weight, idx = best_schedule([])
assert weight == 0.0 and idx == [], f"Empty case failed: ({weight}, {idx})"

# Single job
weight, idx = best_schedule([(0, 1, 5.0)])
assert abs(weight - 5.0) < 1e-12 and idx == [0], f"Single job failed: ({weight}, {idx})"

# All overlapping, pick max weight
jobs = [(0, 5, 10), (0, 3, 20), (2, 6, 15)]
weight, idx = best_schedule(jobs)
# Best should be job 1 (weight 20)
assert abs(weight - 20.0) < 1e-12, f"Expected 20.0, got {weight}"

# Test with touching allowed
jobs = [(0, 1, 5), (1, 2, 5), (2, 3, 5)]
weight, idx = best_schedule(jobs)
assert abs(weight - 15.0) < 1e-12, f"Touching jobs failed: {weight}"

print("All basic tests passed!")
