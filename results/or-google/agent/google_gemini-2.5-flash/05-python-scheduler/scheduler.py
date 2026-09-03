
import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    if not jobs:
        return (0.0, [])

    # Store jobs with their original indices and sort by end time, then start time
    # (end, start, weight, original_index)
    indexed_jobs = []
    for i, (start, end, weight) in enumerate(jobs):
        indexed_jobs.append((end, start, weight, i))
    indexed_jobs.sort()

    n = len(indexed_jobs)
    dp = [0.0] * n
    chosen_jobs_indices = [[] for _ in range(n)]

    # Extract sorted start, end, and weight for easier access
    ends = [job[0] for job in indexed_jobs]
    starts = [job[1] for job in indexed_jobs]
    weights = [job[2] for job in indexed_jobs]
    original_indices = [job[3] for job in indexed_jobs]

    # Precompute p[j]: the latest non-overlapping job before j
    p = [-1] * n
    for j in range(n):
        # Find the rightmost interval i such that ends[i] <= starts[j]
        # bisect_right returns an insertion point which is 1 greater than the index
        # of the last element satisfying the condition.
        # We need to search in the 'ends' array for a value <= starts[j]
        # To use bisect_right, we need to find the index of the first element > starts[j]
        # and then subtract 1 to get the index of the last element <= starts[j].
        # If no such element exists, bisect_right will return 0, and p[j] will remain -1.
        idx = bisect.bisect_right(ends, starts[j])
        # We need to find the largest index k such that ends[k] <= starts[j]
        # bisect_right returns an index where starts[j] could be inserted to maintain order.
        # All elements to the left of this index are <= starts[j].
        # So, we need the rightmost of these.
        # If idx is 0, it means all ends are > starts[j], so no preceding job.
        # Otherwise, idx-1 is the index of the job that ends at or before starts[j].
        if idx > 0:
            # We need to find the largest k such that ends[k] <= starts[j]
            # bisect_right(a, x) returns an insertion point which comes after (to the right of)
            # any existing entries of x in a.
            # So, if we search for starts[j], it will give us the index of the first element
            # strictly greater than starts[j].
            # We need to find the largest index k such that ends[k] <= starts[j].
            # Let's use a custom binary search or adjust bisect_right.

            # A simpler way to find p[j]:
            # Iterate backwards from j-1 to 0 to find the first non-overlapping job.
            # This would be O(N^2) if done naively.
            # With bisect_right on the 'ends' array, we can find the index of the
            # first job whose end time is strictly greater than starts[j].
            # The job just before that (idx - 1) is the one we are looking for.
            # If idx is 0, it means all jobs end after starts[j], so no non-overlapping job.
            
            # The bisect_right function returns an insertion point which comes after (to the right of)
            # any existing entries of x in a.
            # So, if we search for starts[j], it will give us the index of the first element
            # strictly greater than starts[j].
            # The job just before that (idx - 1) is the one we are looking for.
            # If idx is 0, it means all jobs end after starts[j], so no non-overlapping job.
            
            # We need to find the largest index k such that ends[k] <= starts[j].
            # bisect_right(ends, starts[j]) gives the index of the first element in 'ends'
            # that is strictly greater than starts[j].
            # So, the element at (idx - 1) is the largest element in 'ends' that is <= starts[j].
            # This is exactly what we need for p[j].
            p[j] = idx - 1


    # Dynamic Programming
    for i in range(n):
        # Case 1: Don't include job i
        val_not_including_i = dp[i-1] if i > 0 else 0.0

        # Case 2: Include job i
        val_including_i = weights[i]
        if p[i] != -1:
            val_including_i += dp[p[i]]

        if val_including_i > val_not_including_i:
            dp[i] = val_including_i
            # If we include job i, we also include jobs from the optimal schedule up to p[i]
            if p[i] != -1:
                chosen_jobs_indices[i] = chosen_jobs_indices[p[i]] + [original_indices[i]]
            else:
                chosen_jobs_indices[i] = [original_indices[i]]
        else:
            dp[i] = val_not_including_i
            # If we don't include job i, we take the schedule from i-1
            if i > 0:
                chosen_jobs_indices[i] = chosen_jobs_indices[i-1]

    # Reconstruct the optimal set of jobs
    # The chosen_jobs_indices[n-1] will contain the indices, but they might not be sorted by start time.
    # We need to sort them by start time, breaking ties with original index.
    final_chosen_indices = chosen_jobs_indices[n-1]
    
    # To sort by start time, we need the original job data.
    # Create a list of (start_time, original_index) for the chosen jobs.
    sorted_final_chosen_indices_with_start_time = []
    for idx in final_chosen_indices:
        sorted_final_chosen_indices_with_start_time.append((jobs[idx][0], idx)) # (start_time, original_index)
    
    # Sort by start time, then by original index
    sorted_final_chosen_indices_with_start_time.sort()

    # Extract just the original indices
    final_chosen_indices_sorted = [idx for _, idx in sorted_final_chosen_indices_with_start_time]

    return (dp[n-1], final_chosen_indices_sorted)

