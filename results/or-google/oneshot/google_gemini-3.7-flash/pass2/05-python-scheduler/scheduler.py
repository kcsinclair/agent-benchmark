"""Weighted Interval Scheduling at scale."""

from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """Find a non-overlapping subset of jobs that maximizes total weight.

    Parameters
    ----------
    jobs : list[tuple[float, float, float]]
        List of (start, end, weight) tuples.

    Returns
    -------
    tuple[float, list[int]]
        (total_weight, chosen_indices) where chosen_indices are indices into
        the input list sorted by start time (break ties by index ascending).
    """
    if not jobs:
        return (0.0, [])

    n = len(jobs)

    # Sort jobs by end time; keep track of original indices
    # Each item: (start, end, weight, orig_idx)
    sorted_jobs = sorted(
        ((start, end, weight, i) for i, (start, end, weight) in enumerate(jobs)),
        key=lambda item: item[1],
    )

    ends = [item[1] for item in sorted_jobs]

    # dp[i] stores the max weight achievable using a subset of jobs from sorted_jobs[:i]
    dp = [0.0] * (n + 1)
    take = [False] * n
    p_indices = [0] * n

    for i in range(n):
        start, _, weight, _ = sorted_jobs[i]
        # Find latest compatible job ending <= start
        p = bisect_right(ends, start, 0, i) - 1
        p_indices[i] = p

        incl_weight = weight + dp[p + 1]
        excl_weight = dp[i]

        if incl_weight > excl_weight:
            dp[i + 1] = incl_weight
            take[i] = True
        else:
            dp[i + 1] = excl_weight
            take[i] = False

    # Reconstruct chosen jobs
    chosen_indices: list[int] = []
    curr = n
    while curr > 0:
        if take[curr - 1]:
            chosen_indices.append(sorted_jobs[curr - 1][3])
            curr = p_indices[curr - 1] + 1
        else:
            curr -= 1

    # Sort chosen indices by the job's start time, breaking ties by index ascending
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(dp[n]), chosen_indices)
