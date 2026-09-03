"""Weighted interval scheduling module."""

from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """Find a subset of non-overlapping jobs maximizing total weight.

    Args:
        jobs: List of (start, end, weight) tuples.

    Returns:
        (total_weight, chosen_indices) where total_weight is the max achievable
        weight, and chosen_indices are the original indices sorted by start time.
    """
    if not jobs:
        return (0.0, [])

    n = len(jobs)
    # Store jobs with original index: (start, end, weight, orig_idx)
    sorted_jobs = sorted(
        ((s, e, w, idx) for idx, (s, e, w) in enumerate(jobs)),
        key=lambda x: x[1],
    )

    ends = [job[1] for job in sorted_jobs]

    # dp[i] is max weight achievable considering prefix of i jobs (0 to i-1)
    # p_indices[i] stores the bisect index p for job i-1
    dp = [0.0] * (n + 1)
    p_indices = [0] * (n + 1)
    take = [False] * (n + 1)

    for i in range(1, n + 1):
        s, _, w, _ = sorted_jobs[i - 1]
        p = bisect_right(ends, s)
        p_indices[i] = p

        incl_weight = w + dp[p]
        excl_weight = dp[i - 1]

        if incl_weight > excl_weight:
            dp[i] = incl_weight
            take[i] = True
        else:
            dp[i] = excl_weight
            take[i] = False

    # Backtrack to find chosen jobs
    chosen_orig_indices = []
    curr = n
    while curr > 0:
        if take[curr]:
            chosen_orig_indices.append(sorted_jobs[curr - 1][3])
            curr = p_indices[curr]
        else:
            curr -= 1

    # Sort chosen indices by start time ascending, tie-breaking by index ascending
    chosen_orig_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(dp[n]), chosen_orig_indices)
