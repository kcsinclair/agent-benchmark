import bisect
from typing import List, Tuple

def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """
    Weighted interval scheduling – O(n log n) solution.

    Parameters
    ----------
    jobs : list of (start, end, weight)
        Each job has a strict start < end and positive weight.

    Returns
    -------
    (total_weight, chosen_indices)
        total_weight – maximum achievable sum of weights (float)
        chosen_indices – indices of a maximum‑weight subset, sorted by
                         start time (ascending) and then by original index
                         (ascending).
    """
    # Empty input
    if not jobs:
        return 0.0, []

    # Keep original indices
    indexed = [(s, e, w, i) for i, (s, e, w) in enumerate(jobs)]

    # Sort by end time
    indexed.sort(key=lambda x: x[1])

    n = len(indexed)
    ends = [job[1] for job in indexed]          # end times in sorted order
    starts = [job[0] for job in indexed]        # start times (unsorted)
    weights = [job[2] for job in indexed]       # weights (unsorted)
    orig_idx = [job[3] for job in indexed]      # original indices

    # DP arrays
    dp = [0.0] * n          # best weight for prefix ending at i
    taken = [False] * n     # whether job i is taken in the optimal solution for prefix i
    pred = [-1] * n         # predecessor index in sorted order (for backtracking)

    # Base case
    dp[0] = weights[0]
    taken[0] = True
    pred[0] = -1

    # Fill DP
    for i in range(1, n):
        # Find latest job that finishes <= start_i
        # bisect_right returns insertion point after the last <= value
        pos = bisect.bisect_right(ends, starts[i], 0, i)
        p = pos - 1

        # Weight if we take job i
        include = weights[i] + (dp[p] if p >= 0 else 0.0)

        # Choose better of taking i or skipping it
        if include > dp[i - 1]:
            dp[i] = include
            taken[i] = True
        else:
            dp[i] = dp[i - 1]
            taken[i] = False

        pred[i] = p

    # Backtrack to collect chosen original indices
    chosen: List[int] = []
    i = n - 1
    while i >= 0:
        if taken[i]:
            chosen.append(orig_idx[i])
            i = pred[i]          # jump to predecessor
        else:
            i -= 1

    # Sort chosen indices by start time, then by original index
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return float(dp[-1]), chosen
