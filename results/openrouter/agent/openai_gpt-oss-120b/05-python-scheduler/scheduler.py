"""scheduler.py

Efficient weighted interval scheduling.

The module provides a single public function:

    best_schedule(jobs) -> (total_weight, chosen_indices)

where ``jobs`` is a list of ``(start, end, weight)`` tuples.  The function
returns the maximum total weight achievable by a set of non‑overlapping jobs
(and a list of the original indices of one optimal set, sorted by start time).

The implementation runs in O(n log n) time and O(n) memory, suitable for
inputs with up to 200 000 jobs.
"""

from __future__ import annotations

from bisect import bisect_right
from typing import List, Tuple


def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """Return the optimal total weight and a list of chosen job indices.

    Parameters
    ----------
    jobs:
        A list of ``(start, end, weight)`` tuples.  ``start < end`` and
        ``weight > 0`` are guaranteed by the problem statement.

    Returns
    -------
    (total_weight, chosen_indices):
        * ``total_weight`` – the maximum sum of weights (float).
        * ``chosen_indices`` – a list of indices into the original ``jobs``
          list that achieve the optimum.  The list is sorted by the job's
          start time; ties are broken by the original index order.
    """
    if not jobs:
        return 0.0, []

    # Attach original indices so we can recover them after sorting.
    indexed = [(s, e, w, idx) for idx, (s, e, w) in enumerate(jobs)]

    # Sort by end time (primary) and start time (secondary) – the classic order
    # for weighted interval scheduling DP.
    indexed.sort(key=lambda x: (x[1], x[0]))

    n = len(indexed)
    ends = [job[1] for job in indexed]  # list of end times in sorted order

    # dp[i] – best total weight using the first i jobs in the sorted order.
    # dp[0] = 0 (no jobs considered).
    dp: List[float] = [0.0] * (n + 1)
    # p[i] – number of jobs (i.e., dp index) that are compatible with job i-1.
    p: List[int] = [0] * (n + 1)

    for i in range(1, n + 1):
        s, e, w, _ = indexed[i - 1]
        # Find the rightmost job whose end time is <= s (touching is allowed).
        # bisect_right returns the insertion point, which is exactly the count of
        # jobs with end <= s.
        compatible = bisect_right(ends, s)
        p[i] = compatible
        include = w + dp[compatible]
        exclude = dp[i - 1]
        dp[i] = include if include > exclude else exclude

    # Reconstruct one optimal set of jobs.
    chosen: List[int] = []
    i = n
    while i > 0:
        s, e, w, idx = indexed[i - 1]
        if w + dp[p[i]] > dp[i - 1]:
            # Job i-1 is taken.
            chosen.append(idx)
            i = p[i]
        else:
            # Job i-1 is skipped.
            i -= 1

    # ``chosen`` currently holds indices in reverse order of the sorted-by-end list.
    # The required output order is by start time (and then by original index).
    chosen.sort(key=lambda original_idx: (jobs[original_idx][0], original_idx))

    total_weight = dp[n]
    return total_weight, chosen


__all__ = ["best_schedule"]
