# scheduler.py
"""
Weighted interval scheduling for up to 200 000 jobs.

The implementation follows the classic O(n log n) algorithm:
  1. Sort jobs by end time.
  2. For each job find the last non‑overlapping job with binary search.
  3. Dynamic programming over the sorted list.
  4. Reconstruct one optimal set of indices.

The returned indices are sorted by the job's start time (ties by index).
"""

from __future__ import annotations

import bisect
from typing import List, Tuple


def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """
    Return the maximum total weight and one optimal set of job indices.

    Parameters
    ----------
    jobs : list of (start, end, weight)
        All jobs satisfy start < end and weight > 0.

    Returns
    -------
    total_weight : float
        The maximum achievable sum of weights.
    chosen_indices : list[int]
        Indices into the original `jobs` list of one optimal subset,
        sorted by start time (ties by index).
    """
    n = len(jobs)
    if n == 0:
        return 0.0, []

    # Attach original indices and sort by end time
    indexed_jobs = [(s, e, w, idx) for idx, (s, e, w) in enumerate(jobs)]
    indexed_jobs.sort(key=lambda x: x[1])          # sort by end time
    ends = [job[1] for job in indexed_jobs]        # list of end times

    # Pre‑compute p[i] = index of the last job that ends <= start of job i
    p = [0] * n
    for i in range(n):
        start_i = indexed_jobs[i][0]
        j = bisect.bisect_right(ends, start_i) - 1
        p[i] = j  # may be -1 if no compatible job

    # Dynamic programming: M[i] = best weight using first i jobs (sorted by end)
    M = [0.0] * (n + 1)          # M[0] = 0
    take = [False] * n           # whether job i is taken in the optimal solution

    for i in range(1, n + 1):
        w = indexed_jobs[i - 1][2]
        # weight if we take job i-1
        take_weight = w + M[p[i - 1] + 1]
        if take_weight > M[i - 1]:
            M[i] = take_weight
            take[i - 1] = True
        else:
            M[i] = M[i - 1]
            take[i - 1] = False

    total_weight = M[n]

    # Reconstruct one optimal set of indices
    chosen: List[int] = []
    i = n - 1
    while i >= 0:
        if take[i]:
            chosen.append(indexed_jobs[i][3])  # original index
            i = p[i]
        else:
            i -= 1

    # Sort the chosen indices by start time (ties by index)
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return total_weight, chosen
