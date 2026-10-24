from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solve Weighted Interval Scheduling in O(n log n) time.

    Args:
        jobs: list of (start, end, weight) tuples with start < end and weight > 0.

    Returns:
        (total_weight, chosen_indices) where total_weight is a float and
        chosen_indices are original indices sorted by (start, index).
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort jobs by end time ascending
    order = sorted(range(n), key=lambda i: jobs[i][1])
    ends = [jobs[i][1] for i in order]

    # dp[i] = max weight using a subset of the first i sorted jobs
    dp = [0.0] * (n + 1)
    # jump[i] >= 0 means job i (in sorted order) is taken and previous state is jump[i];
    # jump[i] == -1 means job i is skipped.
    jump = [-1] * n

    for i, orig_idx in enumerate(order):
        s, _, w = jobs[orig_idx]
        # Find number of jobs in order[:i] with end <= s
        k = bisect_right(ends, s, 0, i)
        take = dp[k] + w
        skip = dp[i]
        if take > skip:
            dp[i + 1] = take
            jump[i] = k
        else:
            dp[i + 1] = skip

    # Reconstruct optimal subset iteratively
    chosen: list[int] = []
    curr = n - 1
    while curr >= 0:
        k = jump[curr]
        if k >= 0:
            chosen.append(order[curr])
            curr = k - 1
        else:
            curr -= 1

    chosen.sort(key=lambda idx: (jobs[idx][0], idx))
    return (float(dp[n]), chosen)
