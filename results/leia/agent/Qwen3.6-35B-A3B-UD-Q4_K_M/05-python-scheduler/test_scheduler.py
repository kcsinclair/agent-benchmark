from scheduler import best_schedule

# Example from the problem
jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
result = best_schedule(jobs)
print(f"Result: {result}")
print(f"Expected: (13.0, [2, 6])")

# Verify the result
total_weight, chosen_indices = result
print(f"Total weight: {total_weight}")
print(f"Chosen indices: {chosen_indices}")

# Check validity
for idx in chosen_indices:
    start, end, weight = jobs[idx]
    print(f"  Job {idx}: ({start}, {end}, {weight})")

# Check no overlaps
for i in range(len(chosen_indices)):
    for j in range(i + 1, len(chosen_indices)):
        si, ei, wi = jobs[chosen_indices[i]]
        sj, ej, wj = jobs[chosen_indices[j]]
        # They should not overlap: one must start >= the other ends
        if not (si >= ej or sj >= ei):
            print(f"ERROR: Jobs {chosen_indices[i]} and {chosen_indices[j]} overlap!")

# Check weight sum
weight_sum = sum(jobs[idx][2] for idx in chosen_indices)
print(f"Weight sum: {weight_sum}")
print(f"Matches total_weight: {weight_sum == total_weight}")

# Test empty case
print(f"\nEmpty case: {best_schedule([])}")

# Test single job
print(f"Single job: {best_schedule([(1, 2, 5)])}")
