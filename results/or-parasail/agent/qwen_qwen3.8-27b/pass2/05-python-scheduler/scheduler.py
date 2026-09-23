"""Weighted interval scheduling at scale.

Provides :func:`best_schedule`, an O(n log n) solver for the weighted
interval scheduling problem that also reconstructs one optimal subset.
"""

from __future__ import annotations

import bisect


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """Choose a non-overlapping subset of jobs maximizing total weight.

    Parameters
    ----------
    jobs:
        A list of ``(start, end, weight)`` tuples.  Two jobs are compatible
        when one ends at or before the other starts (touching is allowed).

    Returns
    -------
    tuple[float, list[int]]
        ``(total_weight, chosen_indices)`` where ``total_weight`` is the
        maximum achievable weight and ``chosen_indices`` are the indices
        into ``jobs`` of one optimal subset, sorted by start time (ties
        broken by ascending index).
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Order jobs by (end, start, index).  This is the canonical ordering for
    # weighted interval scheduling: the DP processes jobs in increasing end
    # time, and the "compatible predecessor" of a job is the last job that
    # ends at or before it starts.
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))

    # ends[k] is the end time of the k-th job in `order`.  Because `order`
    # is sorted by end time, `ends` is non-decreasing, so binary search works.
    ends = [jobs[i][1] for i in order]

    # dp[k] = best total weight using only the first k jobs in `order`
    # (i.e. jobs order[0..k-1]).  dp[0] = 0.
    dp = [0.0] * (n + 1)
    # take[k] = True if the k-th job (order[k-1]) is included in the optimal
    # solution for the first k jobs.
    take = [False] * (n + 1)

    for k in range(1, n + 1):
        i = order[k - 1]
        s, e, w = jobs[i]

        # p = number of jobs in `order` that end at or before s.
        # bisect_right on the non-decreasing `ends` gives exactly that count.
        p = bisect.bisect_right(ends, s)

        skip = dp[k - 1]
        cand = dp[p] + w
        if cand > skip:
            dp[k] = cand
            take[k] = True
        else:
            dp[k] = skip
            take[k] = False

    # Reconstruct the chosen jobs by walking the DP table backwards.
    chosen: list[int] = []
    k = n
    while k > 0:
        if take[k]:
            chosen.append(order[k - 1])
            i = order[k - 1]
            s = jobs[i][0]
            k = bisect.bisect_right(ends, s)
        else:
            k -= 1

    # Sort by (start, index) as required.
    chosen.sort(key=lambda i: (jobs[i][0], i))

    return (dp[n], chosen)
