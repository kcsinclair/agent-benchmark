from scheduler import best_schedule

# Test with the provided example
jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
result = best_schedule(jobs)
print(f"Result: {result}")
print(f"Expected: (13.0, [2, 6])")

# Verify the result
total_weight, chosen_indices = result
print(f"Total weight: {total_weight}")
print(f"Chosen indices: {chosen_indices}")

# Verify no overlaps
for i in range(len(chosen_indices)):
    for j in range(i+1, len(chosen_indices)):
        idx1, idx2 = chosen_indices[i], chosen_indices[j]
        start1, end1, _ = jobs[idx1]
        start2, end2, _ = jobs[idx2]
        # Check overlap: they overlap if one starts strictly before the other ends
        if start1 < end2 and start2 < end1:
            print(f"ERROR: Jobs {idx1} and {idx2} overlap!")
        else:
            print(f"Jobs {idx1} ({start1}-{end1}) and {idx2} ({start2}-{end2}) don't overlap")

# Verify total weight
actual_weight = sum(jobs[idx][2] for idx in chosen_indices)
print(f"Actual weight from chosen jobs: {actual_weight}")
print(f"Match: {actual_weight == total_weight}")

# Test empty case
result2 = best_schedule([])
print(f"\nEmpty case: {result2}")
print(f"Expected: (0.0, [])")

# Test single job
result3 = best_schedule([(1, 5, 10)])
print(f"\nSingle job: {result3}")
print(f"Expected: (10.0, [0])")
