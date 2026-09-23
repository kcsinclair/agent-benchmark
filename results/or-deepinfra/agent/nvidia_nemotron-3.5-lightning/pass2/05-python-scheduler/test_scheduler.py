from scheduler import best_schedule

# Example from the problem
jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
result = best_schedule(jobs)
print(f"Example result: {result}")
expected = (13.0, [2, 6])
print(f"Expected: {expected}")
print(f"Match: {result == expected}")

# Verify non-overlapping and weight
total_weight, chosen = result
selected = [jobs[i] for i in chosen]
print(f"Selected jobs: {selected}")
# Check no overlap (touching allowed)
for i in range(len(chosen)):
    for j in range(i+1, len(chosen)):
        s1, e1 = jobs[chosen[i]]
        s2, e2 = jobs[chosen[j]]
        # Since chosen are sorted by start, check e1 <= s2
        assert e1 <= s2, f"Overlap: job {chosen[i]} ({s1},{e1}) and job {chosen[j]} ({s2},{e2})"
print("Non-overlapping check passed!")

# Empty case
result_empty = best_schedule([])
print(f"Empty result: {result_empty}")
assert result_empty == (0.0, []), "Empty case failed"
print("Empty case passed!")

# Single job
result_single = best_schedule([(0, 1, 42.0)])
print(f"Single job result: {result_single}")
assert result_single == (42.0, [0]), "Single job case failed"
print("Single job case passed!")
