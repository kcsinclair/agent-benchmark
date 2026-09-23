"""Weighted Interval Scheduling module."""

from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """Find a non-overlapping subset of jobs maximizing total weight.

    Args:
        jobs: List of (start, end, weight) tuples.

    Returns:
        A tuple (total_weight, chosen_indices) where chosen_indices are sorted
        by job start time (tie-broken by index ascending).
    """
    if not jobs:
        return 0.0, []

    n = len(jobs)

    # Sort jobs by end time, tracking their original indices
    # Each entry: (start, end, weight, orig_idx)
    sorted_jobs = sorted(
        ((start, end, weight, i) for i, (start, end, weight) in enumerate(jobs)),
        key=lambda x: x[1],
    )

    ends = [job[1] for job in sorted_jobs]

    # dp[i] stores the maximum weight achievable using a subset of the first i sorted jobs (1-indexed)
    dp = [0.0] * (n + 1)
    take = [False] * (n + 1)
    prev_idx = [0] * (n + 1)

    for i in range(1, n + 1):
        start, _, weight, _ = sorted_jobs[i - 1]

        # Find the last job that finishes at or before this job's start time
        p = bisect_right(ends, start)
        prev_idx[i] = p

        incl_weight = dp[p] + weight
        excl_weight = dp[i - 1]

        if incl_weight > excl_weight:
            dp[i] = incl_weight
            take[i] = True
        else:
            dp[i] = excl_weight
            take[i] = False

    # Traceback to reconstruct the chosen jobs
    chosen_indices: list[int] = []
    curr = n
    while curr > 0:
        if take[curr]:
            chosen_indices.append(sorted_jobs[curr - 1][3])
            curr = prev_idx[curr]
        else:
            curr -= 1

    # Sort chosen indices by start time (breaking ties by original index)
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return float(dp[n]), chosen_indices
