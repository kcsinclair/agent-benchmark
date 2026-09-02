"""
Weighted Interval Scheduling Module.
"""

from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Finds an optimal non-overlapping subset of jobs maximizing total weight.

    Args:
        jobs: A list of (start, end, weight) tuples.

    Returns:
        A tuple of (total_weight, chosen_indices) where:
          - total_weight is the maximum total weight achievable (float).
          - chosen_indices is the list of indices from the input list corresponding
            to the chosen optimal subset, sorted by start time (ties broken by index).
    """
    if not jobs:
        return 0.0, []

    n = len(jobs)

    # Decorate with original index and sort by end time
    # jobs_sorted: list of (start, end, weight, orig_idx)
    jobs_sorted = sorted(
        [(start, end, weight, i) for i, (start, end, weight) in enumerate(jobs)],
        key=lambda x: x[1]
    )

    end_times = [job[1] for job in jobs_sorted]

    # dp[i]: max weight considering a subset of jobs from 0 .. i
    dp = [0.0] * n
    # take[i]: True if job i is included in dp[i], False if dp[i] comes from dp[i-1]
    take = [False] * n
    # prev_compat[i]: latest compatible job index (< i) for job i
    prev_compat = [-1] * n

    for i in range(n):
        start_i, _, weight_i, _ = jobs_sorted[i]

        # Find the latest job j < i with end_times[j] <= start_i
        # bisect_right returns insertion point; subtracting 1 gives the largest index <= start_i
        j = bisect_right(end_times, start_i, 0, i) - 1
        prev_compat[i] = j

        incl_weight = weight_i + (dp[j] if j >= 0 else 0.0)
        excl_weight = dp[i - 1] if i > 0 else 0.0

        if incl_weight > excl_weight:
            dp[i] = incl_weight
            take[i] = True
        else:
            dp[i] = excl_weight
            take[i] = False

    # Reconstruct optimal subset iteratively (prevents recursion limit issues)
    chosen_indices: list[int] = []
    curr = n - 1
    while curr >= 0:
        if take[curr]:
            chosen_indices.append(jobs_sorted[curr][3])
            curr = prev_compat[curr]
        else:
            curr -= 1

    # Sort chosen indices by start time, breaking ties by index ascending
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return float(dp[-1]), chosen_indices
