"""Weighted Interval Scheduling implementation.

This module provides a single function ``best_schedule`` that solves the
weighted interval scheduling problem in O(n log n) time.

The implementation follows the classic dynamic programming approach:

1. Sort jobs by end time.
2. For each job compute ``p[i]`` – the index of the last job that ends
   before the current job starts (binary search on the sorted end times).
3. Run a DP that decides for each job whether to take it or skip it.
4. Reconstruct one optimal subset of job indices.

The function returns the maximum total weight and a list of indices into the
original input list, sorted by start time (ties broken by index).  The list
is guaranteed to be a valid non‑overlapping subset achieving the optimum.
"""

from __future__ import annotations

from bisect import bisect_right
from typing import List, Tuple

__all__ = ["best_schedule"]


def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """Return the maximum total weight and a corresponding optimal subset.

    Parameters
    ----------
    jobs:
        List of ``(start, end, weight)`` tuples.  ``start < end`` and
        ``weight > 0`` are guaranteed.

    Returns
    -------
    total_weight:
        The maximum achievable sum of weights.
    chosen_indices:
        List of indices into the input ``jobs`` list that form an optimal
        non‑overlapping subset, sorted by job start time (ties broken by
        index ascending).
    """
    n = len(jobs)
    if n == 0:
        return 0.0, []

    # Attach original indices and sort by end time.
    jobs_with_index = [(s, e, w, i) for i, (s, e, w) in enumerate(jobs)]
    jobs_with_index.sort(key=lambda x: x[1])  # sort by end time

    starts = [s for s, _, _, _ in jobs_with_index]
    ends = [e for _, e, _, _ in jobs_with_index]
    weights = [w for _, _, w, _ in jobs_with_index]
    orig_idx = [i for _, _, _, i in jobs_with_index]

    # Compute p array: for each job i, find the last job that ends <= starts[i]
    p = [0] * n
    for i in range(n):
        # bisect_right returns insertion point to keep ends sorted
        j = bisect_right(ends, starts[i]) - 1
        p[i] = j  # may be -1 if no compatible job

    # DP arrays
    dp = [0.0] * (n + 1)  # dp[0] = 0
    choice = [False] * (n + 1)  # choice[i] indicates if job i-1 is taken

    for i in range(1, n + 1):
        # Option 1: skip current job
        opt1 = dp[i - 1]
        # Option 2: take current job
        prev_index = p[i - 1] + 1  # shift to dp index
        opt2 = weights[i - 1] + dp[prev_index]
        if opt2 > opt1:
            dp[i] = opt2
            choice[i] = True
        else:
            dp[i] = opt1
            choice[i] = False

    total_weight = dp[n]

    # Reconstruct chosen indices
    chosen = []
    i = n
    while i > 0:
        if choice[i]:
            chosen.append(orig_idx[i - 1])
            i = p[i - 1] + 1
        else:
            i -= 1

    # Sort chosen indices by start time (and index to break ties)
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return total_weight, chosen

# End of module
