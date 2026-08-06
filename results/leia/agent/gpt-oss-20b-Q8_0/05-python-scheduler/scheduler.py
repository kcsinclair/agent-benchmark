"""Weighted Interval Scheduling implementation.

This module provides a single function ``best_schedule`` that solves the
classic weighted interval scheduling problem in O(n log n) time.

The implementation follows the standard dynamic‑programming approach:

1. Sort jobs by end time.
2. For each job compute ``p[i]`` – the index of the last job that ends
   no later than the start of job ``i``.  This is done with a binary
   search on the sorted end times.
3. Run a linear DP that decides whether to take or skip each job.
4. Back‑track to recover one optimal set of job indices.
5. Return the total weight and the indices sorted by start time.

The function is fully iterative and uses only the Python standard
library, satisfying the performance constraints for up to 200 000 jobs.
"""

from __future__ import annotations

from bisect import bisect_right
from typing import List, Tuple

__all__ = ["best_schedule"]


def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """Return the maximum total weight and a corresponding set of job indices.

    Parameters
    ----------
    jobs:
        A list of ``(start, end, weight)`` tuples.  ``start < end`` and
        ``weight > 0`` are guaranteed.

    Returns
    -------
    total_weight:
        The maximum achievable sum of weights.
    chosen_indices:
        A list of indices into the original ``jobs`` list that form a
        non‑overlapping optimal schedule.  The list is sorted by the
        start time of the jobs (ties broken by the original index).

    Notes
    -----
    * The function runs in ``O(n log n)`` time and ``O(n)`` memory.
    * It is fully iterative; no recursion is used.
    * The implementation is deterministic and will always return a
      valid optimal subset.
    """

    n = len(jobs)
    if n == 0:
        return 0.0, []

    # Attach original indices and sort by end time.
    # Each entry: (end, start, weight, orig_index)
    sorted_jobs = sorted(
        [(end, start, weight, idx) for idx, (start, end, weight) in enumerate(jobs)],
        key=lambda x: x[0],
    )

    ends = [job[0] for job in sorted_jobs]

    # Compute p[i] for each job: last job that ends <= start of job i.
    p = []
    for end, start, weight, idx in sorted_jobs:
        # bisect_right returns insertion point; subtract 1 to get last <= start.
        j = bisect_right(ends, start) - 1
        p.append(j)

    # DP arrays: dp[i] is best weight using first i jobs (sorted by end).
    dp = [0.0] * (n + 1)
    take = [False] * (n + 1)  # take[i] indicates if job i-1 is taken in optimal for dp[i]

    for i in range(1, n + 1):
        end, start, weight, idx = sorted_jobs[i - 1]
        incl = weight + dp[p[i - 1] + 1]  # p[i-1] may be -1
        excl = dp[i - 1]
        if incl > excl:
            dp[i] = incl
            take[i] = True
        else:
            dp[i] = excl
            take[i] = False

    total_weight = dp[n]

    # Reconstruct chosen indices.
    chosen = []
    i = n
    while i > 0:
        if take[i]:
            end, start, weight, idx = sorted_jobs[i - 1]
            chosen.append(idx)
            i = p[i - 1] + 1
        else:
            i -= 1

    # Sort chosen indices by start time (and by index to break ties).
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return total_weight, chosen

# End of module
