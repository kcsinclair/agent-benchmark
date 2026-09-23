"""Weighted interval scheduling at scale.

Provides :func:`best_schedule`, an O(n log n) solver for the weighted
interval scheduling problem that also reconstructs one optimal subset.
"""

from __future__ import annotations

import bisect


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """Return ``(total_weight, chosen_indices)`` for the optimal non-overlapping
    subset of ``jobs``.

    ``jobs`` is a list of ``(start, end, weight)`` tuples.  Two jobs are
    compatible when one ends at or before the other starts (touching is
    allowed).  ``chosen_indices`` are indices into the input list, sorted by
    the job's start time (ties broken by ascending index).
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Order jobs by (end, start, index).  This is the canonical order for the
    # weighted interval scheduling DP: when processing job i, every job that
    # could precede it has already been processed.
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))

    # ends[k] is the end time of the k-th job in `order`.  Because the order is
    # sorted by end time, `ends` is non-decreasing, so bisect works on it.
    ends = [jobs[i][1] for i in order]

    # dp[k] = best total weight using only the first k jobs in `order`
    # (i.e. jobs order[0..k-1]).  dp[0] = 0.
    dp = [0.0] * (n + 1)
    # take[k] = True if the k-th job in `order` (order[k-1]) is part of the
    # optimal solution for the first k jobs.
    take = [False] * (n + 1)

    for k in range(1, n + 1):
        i = order[k - 1]
        s, e, w = jobs[i]
        # p = number of jobs in `order` that end at or before s.  These are
        # exactly the jobs compatible with job i.
        p = bisect.bisect_right(ends, s, 0, k - 1)
        skip = dp[k - 1]
        cand = dp[p] + w
        if cand > skip:
            dp[k] = cand
            take[k] = True
        else:
            dp[k] = skip

    # Reconstruct the chosen jobs by walking the DP table backwards.
    chosen = []
    k = n
    while k > 0:
        if take[k]:
            chosen.append(order[k - 1])
            i = order[k - 1]
            s = jobs[i][0]
            p = bisect.bisect_right(ends, s, 0, k - 1)
            k = p
        else:
            k -= 1

    # Sort chosen indices by (start, index) as required.
    chosen.sort(key=lambda i: (jobs[i][0], i))

    return (dp[n], chosen)
