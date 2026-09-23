# scheduler.py

from bisect import bisect_right
from typing import List, Tuple


def best_schedule(jobs: list[tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """
    Weighted interval scheduling (weighted interval selection) in O(n log n).

    Args:
        jobs: list of (start, end, weight) tuples.  start < end, weight > 0.

    Returns:
        (total_weight, chosen_indices) where chosen_indices are indices into
        the original input list, sorted by start time (ties broken by index ascending).
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Attach original index and sort by (end, start, index) to make DP deterministic.
    indexed = [(s, e, w, i) for i, (s, e, w) in enumerate(jobs)]
    indexed.sort(key=lambda x: (x[1], x[0], x[3]))  # sort by end, then start, then original index

    m = n  # number of jobs after sorting; we will work with 1..m in DP arrays

    # p[i] = largest index j < i such that job j ends <= job i starts (touching allowed).
    # We use 1‑based indexing for convenience: p[1..m].
    ends = [0.0] * (m + 1)          # end times, 1‑based
    starts = [0.0] * (m + 1)        # start times, 1‑based
    weights = [0.0] * (m + 1)       # weights, 1‑based
    orig_idx = [0] * (m + 1)        # original index of the job at position i (1‑based)

    for i, (s, e, w, orig) in enumerate(indexed, start=1):
        ends[i] = e
        starts[i] = s
        weights[i] = w
        orig_idx[i] = orig

    # Compute p[i] for i = 1..m using binary search on the sorted end times.
    # p[i] is the count of jobs (in sorted order) that finish <= starts[i].
    p = [0] * (m + 1)
    for i in range(1, m + 1):
        # bisect_right returns the insertion point to the right of any equal ends.
        # Since ends[1..i-1] are sorted, this gives the number of compatible jobs.
        p[i] = bisect_right(ends, starts[i], 1, i)  # search in [1, i)

    # DP arrays: dp[i] = optimal weight using jobs 1..i (sorted order).
    dp = [0.0] * (m + 1)
    # choice[i] = True if job i is included in the optimal solution for prefix i.
    choice = [False] * (m + 1)

    for i in range(1, m + 1):
        incl = weights[i] + dp[p[i]]
        excl = dp[i - 1]
        if incl > excl:
            dp[i] = incl
            choice[i] = True
        else:
            dp[i] = excl
            choice[i] = False

    # Reconstruct chosen jobs (they are in sorted order).
    chosen_sorted: List[int] = []
    i = m
    while i > 0:
        if choice[i]:
            chosen_sorted.append(orig_idx[i])
            i = p[i]
        else:
            i -= 1

    # Sort chosen indices by start time, breaking ties by original index ascending.
    chosen_sorted.sort(key=lambda idx: (jobs[idx][0], idx))

    total_weight = dp[m]
    return (float(total_weight), chosen_sorted)
