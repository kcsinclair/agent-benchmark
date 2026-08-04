"""Test the scheduler module."""

from scheduler import best_schedule

# Example from the problem
jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
result = best_schedule(jobs)
print(f"Result: {result}")
print(f"Expected: (13.0, [2, 6])")
print(f"Weight matches: {result[0] == 13.0}")

# Verify the chosen subset is valid
chosen = result[1]
print(f"\nChosen jobs:")
for idx in chosen:
    print(f"  Job {idx}: {jobs[idx]}")

# Check no overlaps
valid = True
for i in range(len(chosen)):
    for j in range(i + 1, len(chosen)):
        s1, e1, w1 = jobs[chosen[i]]
        s2, e2, w2 = jobs[chosen[j]]
        # Two jobs overlap if one starts strictly before the other ends
        if s1 < e2 and s2 < e1:
            print(f"ERROR: Jobs {chosen[i]} and {chosen[j]} overlap!")
            valid = False

# Verify total weight
total = sum(jobs[idx][2] for idx in chosen)
print(f"\nTotal weight: {total}")
print(f"Matches claimed: {total == result[0]}")
print(f"Subset valid: {valid}")

# Test empty input
print(f"\nEmpty input: {best_schedule([])}")

# Test single job
print(f"Single job: {best_schedule([(0, 5, 10)])}")

# Test non-overlapping jobs
jobs2 = [(0, 1, 5), (1, 2, 3), (2, 3, 7)]
print(f"Non-overlapping: {best_schedule(jobs2)}")

# Test all overlapping
jobs3 = [(0, 5, 10), (1, 6, 20), (2, 7, 15)]
print(f"All overlapping: {best_schedule(jobs3)}")
