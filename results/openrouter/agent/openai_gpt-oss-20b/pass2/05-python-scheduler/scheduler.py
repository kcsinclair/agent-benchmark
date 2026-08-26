"""
Weighted Interval Scheduling implementation.

The module exposes a single function `best_schedule` that solves the
classic weighted interval scheduling problem in O(n log n) time.

The implementation follows the standard dynamic‑programming approach
sorted by job end times and uses binary search to find the last
compatible job for each job.

The function returns the maximum total weight and one optimal set of
job indices sorted by start time.
"""

from __future__ import annotations

from bisect import bisect_right
from typing import List, Tuple

__all__ = ["best_schedule"]


def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """Return the maximum weight and a corresponding optimal subset.

    Parameters
    ----------
    jobs:
        List of tuples ``(start, end, weight)``.  ``start < end`` and
        ``weight > 0`` are guaranteed.

    Returns
    -------
    total_weight:
        The maximum achievable sum of weights.
    chosen_indices:
        List of indices into the original ``jobs`` list that form an
        optimal, non‑overlapping subset.  The list is sorted by the
        job's start time (ties broken by index ascending).

    Notes
    -----
    * The algorithm runs in ``O(n log n)`` time and ``O(n)`` memory.
    * It is fully iterative and does not rely on recursion.
    * The function is safe to import; it has no side effects.
    """

    n = len(jobs)
    if n == 0:
        return 0.0, []

    # Attach original indices and sort by end time.
    jobs_with_index: List[Tuple[float, float, float, int]] = [
        (s, e, w, i) for i, (s, e, w) in enumerate(jobs)
    ]
    jobs_with_index.sort(key=lambda x: x[1])  # sort by end time

    # Pre‑compute end times for binary search.
    ends = [e for _, e, _, _ in jobs_with_index]

    # Compute p[i] = index of last job that ends <= start_i, or -1.
    p: List[int] = []
    for s, _, _, _ in jobs_with_index:
        idx = bisect_right(ends, s) - 1
        p.append(idx)

    # DP array: dp[i] = max weight using first i jobs (sorted by end).
    dp = [0.0] * (n + 1)
    for i in range(1, n + 1):
        s, e, w, _ = jobs_with_index[i - 1]
        incl = w + dp[p[i - 1] + 1]  # p[i-1] may be -1 -> dp[0]
        excl = dp[i - 1]
        dp[i] = incl if incl > excl else excl

    total_weight = dp[n]

    # Reconstruct one optimal subset.
    chosen: List[int] = []
    i = n
    while i > 0:
        if dp[i] == dp[i - 1]:
            i -= 1
        else:
            # Include job i-1
            chosen.append(jobs_with_index[i - 1][3])  # original index
            i = p[i - 1] + 1

    # The chosen indices are in reverse order of end times.
    # Sort them by start time (and index for ties) as required.
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return total_weight, chosen

# End of module
