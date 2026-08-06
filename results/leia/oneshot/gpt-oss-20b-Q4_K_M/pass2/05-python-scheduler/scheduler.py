and returns the maximum total weight together with one optimal
subset of job indices (indices into the original list).  The indices
are sorted by the job’s start time (ties broken by the original index).

The implementation follows the classic dynamic‑programming approach
with binary search for the previous compatible job.  All data structures
are built iteratively, so the recursion limit is never touched.
"""

from __future__ import annotations
from bisect import bisect_right
from typing import List, Tuple

__all__ = ["best_schedule"]


def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """
    Return the maximum achievable total weight and a list of indices of
    jobs that realise this weight.

    Parameters
    ----------
    jobs : list[tuple[float, float, float]]
        Each tuple is (start, end, weight).  All starts < ends and
        all weights > 0.

    Returns
    -------
    tuple[float, list[int]]
        (total_weight, chosen_indices)

        * ``total_weight`` – the maximum sum of weights (float).
        * ``chosen_indices`` – indices into the original ``jobs`` list,
          sorted by start time (ties by index ascending).

    Notes
    -----
    * The algorithm runs in O(n log n) time and O(n) memory.
    * For an empty input the function returns ``(0.0, [])``.
    """
    n = len(jobs)
    if n == 0:
        return 0.0, []

    # ------------------------------------------------------------------
    # 1.  Sort jobs by end time (stable – keeps original index order)
    # ------------------------------------------------------------------
    #   We keep the original index so we can return it later.
    sorted_jobs = sorted(
        [(s, e, w, i) for i, (s, e, w) in enumerate(jobs)],
        key=lambda x: x[1]          # sort by end
    )

    # ------------------------------------------------------------------
    # 2.  Prepare arrays for DP
    # ------------------------------------------------------------------
    ends = [e for (_, e, _, _) in sorted_jobs]          # end times in sorted order
    dp = [0.0] * (n + 1)                                 # dp[0] = 0
    prev = [-1] * (n + 1)                                 # reconstruction helper

    # ------------------------------------------------------------------
    # 3.  DP loop
    # ------------------------------------------------------------------
    for i in range(1, n + 1):
        s, e, w, orig_idx = sorted_jobs[i - 1]
        # Find the last job that ends <= start time s
        p = bisect_right(ends, s) - 1          # p is 0‑based index, -1 if none
        include = w + dp[p + 1]               # dp index is number of jobs considered
        skip = dp[i - 1]

        if include > skip:                     # choose include
            dp[i] = include
            prev[i] = p + 1                    # previous job considered
        else:                                   # choose skip
            dp[i] = skip
            prev[i] = i - 1

    # ------------------------------------------------------------------
    # 4.  Reconstruct chosen indices
    # ------------------------------------------------------------------
    chosen = []
    i = n
    while i > 0:
        if prev[i] == i - 1:          # we skipped this job
            i -= 1
        else:                           # we included this job
            _, _, _, orig_idx = sorted_jobs[i - 1]
            chosen.append(orig_idx)
            i = prev[i]

    # ------------------------------------------------------------------
    # 5.  Sort chosen indices by start time (ties by index)
    # ------------------------------------------------------------------
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return dp[n], chosen


# ----------------------------------------------------------------------
# The following test is executed only when the module is run directly.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Example from the problem statement
    jobs = [
        (1, 4, 5),
        (3, 5, 1),
        (0, 6, 8),
        (4, 7, 4),
        (3, 9, 6),
        (5, 10, 3),
        (6, 11, 5),
    ]
    total, indices = best_schedule(jobs)
    print("Total weight:", total)
    print("Chosen indices:", indices)
    # Expected output: 13.0 and [2, 6]
