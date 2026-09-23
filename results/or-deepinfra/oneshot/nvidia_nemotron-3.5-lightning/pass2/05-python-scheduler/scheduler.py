# scheduler.py

from bisect import bisect_right
from typing import List, Tuple


def best_schedule(jobs: list[tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """
    Weighted interval scheduling (weighted interval selection) in O(n log n).

    Args:
        jobs: list of (start, end, weight) tuples.  start < end, weight > 0.

    Returns:
        (total_weight, chosen_indices) where chosen_indices are the original
        indices of an optimal subset, sorted by start time (ties broken by
        index ascending).
    """
    n = len(jobs)
    if n == 0:
        return 0.0, []

    # Attach original index and sort by (end, start, index) to make DP deterministic.
    indexed = [(s, e, w, i) for i, (s, e, w) in enumerate(jobs)]
    indexed.sort(key=lambda x: (x[1], x[0], x[3]))  # sort by end, then start, then index

    m = n  # number of jobs after sorting; we will use 1‑based DP for convenience
    # ends[i] = end time of the i‑th job in sorted order (1‑based)
    # starts[i] = start time of the i‑th job in sorted order
    # weights[i] = weight of the i‑th job in sorted order
    ends: List[float] = [0.0] * (m + 1)
    starts: List[float] = [0.0] * (m + 1)
    weights: List[float] = [0.0] * (m + 1)
    orig_idx: List[int] = [0] * (m + 1)

    for i, (s, e, w, orig_i) in enumerate(indexed, start=1):
        ends[i] = e
        starts[i] = s
        weights[i] = w
        orig_idx[i] = orig_i

    # p[i] = largest index j < i such that job j ends <= job i starts (touching allowed)
    # binary search on the sorted end times.
    p: List[int] = [0] * (m + 1)
    for i in range(1, m + 1):
        # we need the rightmost j with ends[j] <= starts[i]
        # bisect_right returns the insertion point after any existing entries equal to starts[i],
        # so we subtract 1 to get the count of jobs ending <= starts[i].
        j = bisect_right(ends, starts[i], 1, i) - 1
        p[i] = j

    # DP arrays: dp[i] = optimal weight using jobs 1..i (sorted)
    dp: List[float] = [0.0] * (m + 1)
    # choice[i] = True if job i is included in the optimal solution for prefix i
    choice: List[bool] = [False] * (m + 1)

    for i in range(1, m + 1):
        incl = weights[i] + dp[p[i]]
        excl = dp[i - 1]
        if incl > excl:
            dp[i] = incl
            choice[i] = True
        else:
            dp[i] = excl
            choice[i] = False

    # Reconstruct chosen jobs
    chosen_sorted: List[int] = []  # will hold original indices in sorted‑processing order
    i = m
    while i > 0:
        if choice[i]:
            chosen_sorted.append(orig_idx[i])
            i = p[i]
        else:
            i -= 1

    # chosen_sorted currently has indices from last to first; reverse to get chronological order.
    chosen_sorted.reverse()

    # Final sorting requirement: sort by start time, break ties by index ascending.
    # The jobs are already in order of processing (which is by end time), but the
    # specification asks for sorting by start time.  We perform a final sort.
    chosen_sorted.sort(key=lambda idx: (jobs[idx][0], idx))

    return float(dp[m]), chosen_sorted
