import bisect


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    if not jobs:
        return (0.0, [])

    n = len(jobs)

    # Create a list of (end_time, original_index) for binary search
    # We'll sort jobs by end time for the DP
    indexed_jobs = list(range(n))
    # Sort by end time, then by start time, then by index for stability
    indexed_jobs.sort(key=lambda i: (jobs[i][1], jobs[i][0], i))

    # Create arrays for sorted jobs
    sorted_starts = [jobs[i][0] for i in indexed_jobs]
    sorted_ends = [jobs[i][1] for i in indexed_jobs]
    sorted_weights = [jobs[i][2] for i in indexed_jobs]

    # For each job in sorted order, find the latest job that doesn't overlap
    # Two jobs overlap if one starts strictly before the other ends.
    # So job j (with end time sorted_ends[j]) is compatible with job i (with start time sorted_starts[i])
    # if sorted_starts[i] >= sorted_ends[j].
    # We want the latest such job j < i (in sorted order).

    # Precompute p[i] = index of the latest job in sorted order that ends <= sorted_starts[i]
    # We use binary search on sorted_ends for this.

    p = [0] * n
    for i in range(n):
        # Find the rightmost job j < i such that sorted_ends[j] <= sorted_starts[i]
        # bisect_right gives us the insertion point; we want the element just before it
        pos = bisect.bisect_right(sorted_ends, sorted_starts[i], 0, i)
        if pos == 0:
            p[i] = -1  # No compatible previous job
        else:
            p[i] = pos - 1

    # DP: dp[i] = maximum weight using a subset of jobs[0..i] (in sorted order)
    # dp[i] = max(dp[i-1], sorted_weights[i] + (dp[p[i]] if p[i] >= 0 else 0))

    dp = [0.0] * n
    dp[0] = sorted_weights[0]

    for i in range(1, n):
        include = sorted_weights[i]
        if p[i] >= 0:
            include += dp[p[i]]
        exclude = dp[i - 1]
        dp[i] = max(include, exclude)

    total_weight = dp[n - 1]

    # Backtrack to find which jobs were chosen
    chosen_sorted_indices = []
    i = n - 1
    while i >= 0:
        include = sorted_weights[i]
        if p[i] >= 0:
            include += dp[p[i]]
        if include >= dp[i]:
            # Job i was included
            chosen_sorted_indices.append(i)
            if p[i] >= 0:
                i = p[i]
            else:
                i = -1
        else:
            # Job i was not included
            i -= 1

    # chosen_sorted_indices contains indices into the sorted arrays
    # Convert back to original indices
    chosen_original_indices = [indexed_jobs[i] for i in chosen_sorted_indices]

    # Sort by start time, breaking ties by original index ascending
    chosen_original_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (total_weight, chosen_original_indices)
