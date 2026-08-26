"""
Weighted interval scheduling for large inputs.

The implementation follows the classic dynamic programming solution
sorted by end time.  The algorithm runs in O(n log n) time and uses
O(n) additional memory, which satisfies the constraints for up to
200 000 jobs.

The function ``best_schedule`` accepts a list of ``(start, end, weight)``
tuples and returns a tuple ``(total_weight, chosen_indices)`` where
``chosen_indices`` are indices into the original input list.

The implementation is fully iterative and uses only the Python
standard library.
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
        List of ``(start, end, weight)`` tuples.  ``start < end`` and
        ``weight > 0`` are guaranteed.

    Returns
    -------
    total_weight:
        The maximum achievable sum of weights.
    chosen_indices:
        A list of indices into the original ``jobs`` list that form a
        non‑overlapping subset achieving ``total_weight``.  The list is
        sorted by the job's start time; ties are broken by the original
        index.

    Notes
    -----
    * The function is iterative and runs in ``O(n log n)`` time.
    * It uses only the standard library.
    * If ``jobs`` is empty, ``(0.0, [])`` is returned.
    """

    n = len(jobs)
    if n == 0:
        return 0.0, []

    # Attach original indices and sort by end time.
    sorted_jobs = [(*job, idx) for idx, job in enumerate(jobs)]
    sorted_jobs.sort(key=lambda x: x[1])  # sort by end time

    # Extract end times for binary search.
    end_times = [job[1] for job in sorted_jobs]

    # Compute p[j] = index of last job that ends <= start of job j.
    p = []  # length n, values are -1 or 0..n-1
    for j, job in enumerate(sorted_jobs):
        start_j = job[0]
        # bisect_right returns insertion point; subtract 1 to get last <= start
        idx = bisect_right(end_times, start_j) - 1
        p.append(idx)

    # DP arrays: dp[i] = best weight using first i jobs (sorted by end)
    dp = [0.0] * (n + 1)
    choose_incl = [False] * (n + 1)  # whether job i-1 is included in optimal for dp[i]

    for j in range(n):  # j is 0-based index in sorted_jobs
        weight_j = sorted_jobs[j][2]
        incl = weight_j
        if p[j] != -1:
            incl += dp[p[j] + 1]
        excl = dp[j]
        if incl > excl:
            dp[j + 1] = incl
            choose_incl[j + 1] = True
        else:
            dp[j + 1] = excl
            choose_incl[j + 1] = False

    # Reconstruct chosen indices.
    chosen = []
    i = n
    while i > 0:
        if choose_incl[i]:
            job = sorted_jobs[i - 1]
            chosen.append(job[3])  # original index
            i = p[i - 1] + 1 if p[i - 1] != -1 else 0
        else:
            i -= 1

    # Sort chosen indices by start time (and index to break ties).
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    total_weight = dp[n]
    return total_weight, chosen

# The module has no side effects on import.

"""
End of file.
"""
