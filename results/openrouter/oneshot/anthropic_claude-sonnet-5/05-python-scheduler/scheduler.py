"""
scheduler.py

Weighted Interval Scheduling solved in O(n log n) time using dynamic
programming over jobs sorted by end time, with binary search (via
bisect) to find the latest compatible predecessor for each job.
"""

import bisect


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort jobs by end time, keeping track of original indices.
    # order[i] = original index of the i-th job when sorted by end time.
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0]))

    starts = [jobs[i][0] for i in order]
    ends = [jobs[i][1] for i in order]
    weights = [jobs[i][2] for i in order]

    # dp[i] = max weight achievable using first i jobs (sorted order), 0-indexed dp[0]=0
    # dp[i] corresponds to considering job (i-1) in sorted order.
    dp = [0.0] * (n + 1)
    # choice[i] = True if job (i-1) in sorted order is included in the optimal solution for dp[i]
    choice = [False] * (n + 1)
    # prev_take[i] = index (in dp array, i.e. number of jobs considered) that we transition
    # from when we take job (i-1). Used for reconstruction.
    prev_index = [0] * (n + 1)  # p(i): number of jobs (in sorted order) compatible before job i-1

    # For binary search: ends array is sorted (since sorted by end time ascending,
    # but there could be ties; strict overlap rule: compatible if start >= end of prev)
    # We need for job i (0-indexed in sorted order), find the largest index j such that
    # ends[j] <= starts[i]. Since job ending at t is compatible with job starting at t.

    for i in range(1, n + 1):
        job_start = starts[i - 1]
        job_weight = weights[i - 1]

        # Find largest j in [0, i-1) such that ends[j] <= job_start
        # ends[0..i-2] are the ends of jobs before this one in sorted order
        # bisect_right on ends[0:i-1] for value job_start gives count of ends <= job_start
        j = bisect.bisect_right(ends, job_start, 0, i - 1)
        prev_index[i] = j

        take_weight = job_weight + dp[j]
        skip_weight = dp[i - 1]

        if take_weight > skip_weight:
            dp[i] = take_weight
            choice[i] = True
        else:
            dp[i] = skip_weight
            choice[i] = False

    total_weight = dp[n]

    # Reconstruct solution iteratively
    chosen_sorted_positions = []  # positions in sorted order (0-indexed) that are chosen
    i = n
    while i > 0:
        if choice[i]:
            chosen_sorted_positions.append(i - 1)
            i = prev_index[i]
        else:
            i -= 1

    # Map back to original indices
    chosen_indices = [order[pos] for pos in chosen_sorted_positions]

    # Sort by start time, tie-break by original index ascending
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(total_weight), chosen_indices)
