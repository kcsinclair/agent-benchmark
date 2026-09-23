from __future__ import annotations
from bisect import bisect_right
from typing import List, Tuple

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Weighted interval scheduling in O(n log n) time.

    Args:
        jobs: list of (start, end, weight) tuples.

    Returns:
        (total_weight, chosen_indices) where chosen_indices are indices
        into the input list, sorted by start time (ties broken by index ascending).
    """
    if not jobs:
        return (0.0, [])

    # Attach original index to each job
    indexed = [(s, e, w, i) for i, (s, e, w) in enumerate(jobs)]
    # Sort by end time, then by start time, then by original index for determinism
    indexed.sort(key=lambda x: (x[1], x[0], x[3]))

    n = len(indexed)
    # ends[k] = end time of the k-th job in sorted order (1-indexed for convenience)
    ends: List[float] = [0.0] * (n + 1)
    # dp[k] = optimal weight using first k jobs (k from 0..n)
    dp: List[float] = [0.0] * (n + 1)
    # choice[k] = True if job k-1 is included in the optimal subset for first k jobs
    choice: List[bool] = [False] * (n + 1)

    # Precompute p[k] = largest index j < k such that job j-1 ends <= job k-1 starts
    # p is 1-indexed: p[k] in [0..k-1]
    p: List[int] = [0] * (n + 1)

    for k in range(1, n + 1):
        s, e, w, orig_idx = indexed[k - 1]
        ends[k] = e
        # Find the rightmost job in indexed[0..k-2] with end <= s
        # bisect_right on ends[1..k-1] (which is ends[1:k])
        # We search in the whole ends list but limit by k-1
        j = bisect_right(ends, s, 1, k) - 1  # j is count of jobs ending <= s
        p[k] = j

        # Include job k-1
        include = w + dp[p[k]]
        # Exclude job k-1
        exclude = dp[k - 1]

        if include > exclude:
            dp[k] = include
            choice[k] = True
        else:
            dp[k] = exclude
            choice[k] = False

    # Reconstruct chosen indices
    chosen: List[int] = []
    k = n
    while k > 0:
        if choice[k]:
            # Job k-1 is included
            _, _, _, orig_idx = indexed[k - 1]
            chosen.append(orig_idx)
            k = p[k]
        else:
            k -= 1

    # Sort chosen indices by start time, break ties by index ascending
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    total_weight = dp[n]
    return (float(total_weight), chosen)
