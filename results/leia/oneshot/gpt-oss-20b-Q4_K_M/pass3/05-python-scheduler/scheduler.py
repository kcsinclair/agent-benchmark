and returns the maximum total weight together with one optimal
subset of job indices (indices into the original list).  The indices
are sorted by the job's start time (ties broken by the original
index).  The implementation uses the classic DP with binary search
and runs in ``O(n log n)`` time and ``O(n)`` memory, suitable for
up to 200 000 jobs.
"""

from bisect import bisect_right
from typing import List, Tuple

def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """
    Return the maximum achievable total weight and a list of indices
    of one optimal subset of non‑overlapping jobs.

    Parameters
    ----------
    jobs : list of (start, end, weight)
        All jobs satisfy ``start < end`` and ``weight > 0``.
        The list may be empty.

    Returns
    -------
    total_weight : float
        The maximum total weight.
    chosen_indices : list[int]
        Indices into the original ``jobs`` list of one optimal subset,
        sorted by start time (ties by index ascending).
    """
    n = len(jobs)
    if n == 0:
        return 0.0, []

    # ------------------------------------------------------------------
    # 1.  Sort jobs by end time (stable – keeps original order for ties)
    # ------------------------------------------------------------------
    # We keep the original index for reconstruction.
    sorted_jobs = sorted(
        [(end, start, weight, idx) for idx, (start, end, weight) in enumerate(jobs)],
        key=lambda x: x[0]          # sort by end
    )

    ends = [e for e, _, _, _ in sorted_jobs]          # list of end times
    starts = [s for _, s, _, _ in sorted_jobs]        # list of start times
    weights = [w for _, _, w, _ in sorted_jobs]       # list of weights
    orig_idx = [i for _, _, _, i in sorted_jobs]      # original indices

    # ------------------------------------------------------------------
    # 2.  For each job find the last non‑overlapping job (p[i])
    # ------------------------------------------------------------------
    # p[i] will be an index in 0..i-1 (or 0 if none).  We use 1‑based
    # DP arrays, so p[i] is the number of jobs that end <= start_i.
    p = [0] * (n + 1)          # p[0] unused
    for i in range(1, n + 1):
        # bisect_right returns the insertion point to keep ends sorted.
        # We need the last index j with ends[j] <= starts[i-1]
        j = bisect_right(ends, starts[i - 1])   # j in 0..i-1
        p[i] = j

    # ------------------------------------------------------------------
    # 3.  DP arrays
    # ------------------------------------------------------------------
    dp = [0.0] * (n + 1)          # dp[0] = 0
    choose = [False] * (n + 1)     # choose[i] == True if job i-1 is taken

    for i in range(1, n + 1):
        # Option 1: skip job i-1
        skip = dp[i - 1]
        # Option 2: take job i-1
        take = weights[i - 1] + dp[p[i]]
        if take > skip:
            dp[i] = take
            choose[i] = True
        else:
            dp[i] = skip
            choose[i] = False

    # ------------------------------------------------------------------
    # 4.  Reconstruct one optimal subset
    # ------------------------------------------------------------------
    chosen = []
    i = n
    while i > 0:
        if choose[i]:
            chosen.append(orig_idx[i - 1])   # original index of job i-1
            i = p[i]
        else:
            i -= 1

    # ------------------------------------------------------------------
    # 5.  Sort the chosen indices by start time (ties by index)
    # ------------------------------------------------------------------
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return dp[n], chosen
