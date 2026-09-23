"""Weighted Interval Scheduling implementation."""

from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """Compute the maximum weight non-overlapping subset of jobs.

    Parameters
    ----------
    jobs : list[tuple[float, float, float]]
        A list of tuples (start, end, weight).

    Returns
    -------
    tuple[float, list[int]]
        (total_weight, chosen_indices) where total_weight is the maximum
        achievable weight and chosen_indices are the indices in the original
        jobs list sorted by start time (ties broken by index ascending).
    """
    if not jobs:
        return 0.0, []

    n = len(jobs)

    # Attach original index: (start, end, weight, original_index)
    # Sort primarily by end time ascending
    sorted_jobs = sorted(
        ((start, end, weight, i) for i, (start, end, weight) in enumerate(jobs)),
        key=lambda item: item[1],
    )

    end_times = [job[1] for job in sorted_jobs]

    # dp[i] will store the maximum weight using a subset of sorted_jobs[0..i]
    dp = [0.0] * n
    # take[i] tracks whether sorted_jobs[i] was included in the optimal solution for prefix i
    take = [False] * n
    # p[i] stores the index of the latest compatible job before i
    p = [-1] * n

    for i in range(n):
        start_i, _, weight_i, _ = sorted_jobs[i]

        # Find the latest job j < i with end_times[j] <= start_i
        # bisect_right gives the insertion index, subtract 1 for the job index
        latest_compatible = bisect_right(end_times, start_i, 0, i) - 1
        p[i] = latest_compatible

        include_weight = weight_i + (dp[latest_compatible] if latest_compatible >= 0 else 0.0)
        exclude_weight = dp[i - 1] if i > 0 else 0.0

        if include_weight > exclude_weight:
            dp[i] = include_weight
            take[i] = True
        else:
            dp[i] = exclude_weight
            take[i] = False

    # Reconstruct the chosen jobs iteratively
    chosen_indices: list[int] = []
    curr = n - 1
    while curr >= 0:
        if take[curr]:
            chosen_indices.append(sorted_jobs[curr][3])
            curr = p[curr]
        else:
            curr -= 1

    # Sort chosen indices by job start time, breaking ties by index ascending
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return float(dp[-1]), chosen_indices
