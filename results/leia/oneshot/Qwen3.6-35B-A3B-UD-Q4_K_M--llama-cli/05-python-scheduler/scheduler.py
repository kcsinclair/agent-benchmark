"""Weighted interval scheduling — O(n log n) via DP + binary search."""

import bisect


def best_schedule(jobs):
    """Return (max_weight, chosen_indices) for the optimal non-overlapping subset.

    ``jobs`` is a list of ``(start, end, weight)`` tuples.
    Two jobs overlap when one starts *strictly before* the other ends —
    touching is allowed.
    """
    if not jobs:
        return (0.0, [])

    n = len(jobs)

    # Build indexed jobs: (end, start, weight, original_index), sorted by end time.
    indexed = sorted(
        ((jobs[i][1], jobs[i][0], jobs[i][2], i) for i in range(n)),
        key=lambda x: (x[0], x[3]),
    )

    end_times = [indexed[i][0] for i in range(n)]

    # dp[i] = max weight achievable using the first *i* jobs in the sorted order.
    dp = [0.0] * (n + 1)

    for i in range(n):
        start_i, weight_i = indexed[i][1], indexed[i][2]
        # Find how many of the first *i* jobs end at or before start_i.
        j = bisect.bisect_right(end_times, start_i, 0, i)
        dp[i + 1] = max(dp[i], weight_i + dp[j])

    # ── back-track to reconstruct the optimal subset ────────────────────
    chosen = []
    i = n
    while i > 0:
        start_i, weight_i = indexed[i - 1][1], indexed[i - 1][2]
        j = bisect.bisect_right(end_times, start_i, 0, i - 1)
        if weight_i + dp[j] >= dp[i]:
            chosen.append(indexed[i - 1][3])
            i = j
        else:
            i -= 1

    # Sort by start time, ties broken by original index ascending.
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return (dp[n], chosen)
