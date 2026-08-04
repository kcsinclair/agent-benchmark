"""scheduler.py
Weighted Interval Scheduling (O(n log n))

Provides a single function:
    best_schedule(jobs) -> (total_weight, chosen_indices)
where `jobs` is a list of (start, end, weight) tuples.

The implementation:
* Sorts jobs by end time.
* Uses binary search to find the last non‑overlapping predecessor for each job.
* Dynamic programming (iterative) computes the optimal total weight.
* Reconstructs one optimal set of job indices.
* Returns the indices sorted by start time (ties broken by original index).

The algorithm runs in O(n log n) time and O(n) memory, suitable for up to
200 000 jobs.
"""

from __future__ import annotations

from bisect import bisect_right
from typing import List, Tuple


def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """Return the maximum total weight of a non‑overlapping subset of jobs.

    Parameters
    ----------
    jobs:
        List of ``(start, end, weight)`` tuples. ``start < end`` and ``weight > 0``
        are guaranteed by the problem statement.

    Returns
    -------
    (total_weight, chosen_indices):
        * ``total_weight`` – the optimal sum of weights (float).
        * ``chosen_indices`` – list of original indices of one optimal subset.
          The list is sorted by the job's start time; ties are broken by the
          original index to satisfy the required ordering.
    """
    n = len(jobs)
    if n == 0:
        return 0.0, []

    # Attach original index to each job for later reconstruction.
    indexed_jobs = [(s, e, w, idx) for idx, (s, e, w) in enumerate(jobs)]
    # Sort by end time (primary). Python's sort is stable, so ties keep original order.
    indexed_jobs.sort(key=lambda x: (x[1], x[0]))  # (end, start) – end primary

    # Pre‑compute an array of end times for binary search.
    ends = [job[1] for job in indexed_jobs]

    # predecessor[i] = index of the last job (in sorted order) that finishes
    # no later than the start of job i, or -1 if none.
    predecessor: List[int] = [-1] * n
    for i, (s, e, w, idx) in enumerate(indexed_jobs):
        # bisect_right returns insertion point to keep ends sorted.
        # We need the rightmost end <= s.
        j = bisect_right(ends, s) - 1
        predecessor[i] = j

    # DP arrays: dp[i] = optimal weight using first i jobs (i from 0..n).
    dp: List[float] = [0.0] * (n + 1)
    # decision[i] is True if job i‑1 (the i‑th job in sorted order) is taken.
    decision: List[bool] = [False] * (n + 1)

    for i in range(1, n + 1):
        s, e, w, orig_idx = indexed_jobs[i - 1]
        # Weight if we take this job.
        pred = predecessor[i - 1]
        include_weight = w + dp[pred + 1]  # dp index shift because dp[0] corresponds to "no jobs"
        exclude_weight = dp[i - 1]
        if include_weight > exclude_weight:
            dp[i] = include_weight
            decision[i] = True
        else:
            dp[i] = exclude_weight
            decision[i] = False

    total_weight = dp[n]

    # Reconstruct chosen jobs.
    chosen: List[int] = []
    i = n
    while i > 0:
        if decision[i]:
            s, e, w, orig_idx = indexed_jobs[i - 1]
            chosen.append(orig_idx)
            i = predecessor[i - 1] + 1
        else:
            i -= 1

    # The reconstruction yields indices in reverse order of end time.
    # The specification requires sorting by start time (and then by index).
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return total_weight, chosen

# The module provides no top‑level execution code; it is safe to import.
