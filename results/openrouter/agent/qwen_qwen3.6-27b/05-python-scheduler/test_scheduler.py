"""Test the scheduler module."""

from scheduler import best_schedule

# Example from the problem
jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
result = best_schedule(jobs)
print(f"Result: {result}")
print(f"Expected: (13.0, [2, 6])")
print(f"Match: {result[0] == 13.0}")

# Verify the chosen subset is valid
if result[1]:
    chosen = [jobs[i] for i in result[1]]
    print(f"Chosen jobs: {chosen}")
    # Check no overlaps
    for i in range(len(chosen) - 1):
        if chosen[i][1] > chosen[i+1][0]:
            print(f"ERROR: Overlap between {chosen[i]} and {chosen[i+1]}")
    print(f"Total weight: {sum(j[2] for j in chosen)}")

# Test empty input
print(f"\nEmpty: {best_schedule([])}")

# Test single job
print(f"Single: {best_schedule([(1, 5, 10)])}")

# Test non-overlapping jobs
jobs2 = [(1, 3, 5), (3, 5, 7), (5, 7, 3)]
print(f"Non-overlapping: {best_schedule(jobs2)}")

# Test all overlapping
jobs3 = [(1, 10, 5), (2, 9, 10), (3, 8, 15)]
print(f"All overlapping: {best_schedule(jobs3)}")
