from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """Find a maximum-weight subset of non-overlapping intervals.

    Args:
        jobs: List of (start, end, weight) tuples with start < end and weight > 0.

    Returns:
        A tuple (total_weight, chosen_indices) where total_weight is the maximum
        achievable sum of weights as a float, and chosen_indices are the indices
        into jobs of an optimal subset sorted by (start, index).
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    order = sorted(range(n), key=lambda i: jobs[i][1])
    ends = [jobs[i][1] for i in order]

    dp = [0.0] * (n + 1)
    predecessors = [0] * n

    for k, idx in enumerate(order):
        start, _, weight = jobs[idx]
        p = bisect_right(ends, start, 0, k)
        predecessors[k] = p
        with_job = dp[p] + weight
        without_job = dp[k]
        dp[k + 1] = with_job if with_job > without_job else without_job

    chosen: list[int] = []
    k = n
    while k > 0:
        if dp[k] > dp[k - 1]:
            chosen.append(order[k - 1])
            k = predecessors[k - 1]
        else:
            k -= 1

    chosen.sort(key=lambda i: (jobs[i][0], i))
    return (float(dp[n]), chosen)
