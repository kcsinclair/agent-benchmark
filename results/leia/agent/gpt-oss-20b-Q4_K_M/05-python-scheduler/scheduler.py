"""
Weighted Interval Scheduling – O(n log n) implementation.

The module exposes a single function:

    best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]

which returns the maximum achievable total weight and a list of indices of
jobs from the original input that realise that optimum.  The indices are
sorted by the job start time (ties broken by the original index).

The algorithm is the classic dynamic‑programming solution with binary
search for the predecessor job.  All work is done iteratively so the
Python recursion limit is never hit.
"""

from __future__ import annotations

from bisect import bisect_right
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """Return the optimal weighted schedule.

    Parameters
    ----------
    jobs : list of (start, end, weight)
        All values are assumed to satisfy ``start < end`` and ``weight > 0``.

    Returns
    -------
    (total_weight, chosen_indices) : tuple
        * ``total_weight`` – the maximum achievable sum of weights (float).
        * ``chosen_indices`` – a list of indices into the original ``jobs``
          list that form one optimal non‑overlapping subset.  The list is
          sorted by the job start time; if two jobs share the same start
          time the smaller original index comes first.

    Notes
    -----
    * The function runs in ``O(n log n)`` time and ``O(n)`` memory.
    * For an empty input ``(0.0, [])`` is returned.
    """
    n = len(jobs)
    if n == 0:
        return 0.0, []

    # ---------------------------------------------------------------------
    # 1.  Sort jobs by end time (stable to preserve original indices).
    # ---------------------------------------------------------------------
    # We keep the original index so we can return it later.
    sorted_jobs = sorted(
        [(s, e, w, idx) for idx, (s, e, w) in enumerate(jobs)],
        key=lambda x: x[1],  # end time
    )

    starts = [s for s, _, _, _ in sorted_jobs]
    ends = [e for _, e, _, _ in sorted_jobs]
    weights = [w for _, _, w, _ in sorted_jobs]
    orig_indices = [idx for _, _, _, idx in sorted_jobs]

    # ---------------------------------------------------------------------
    # 2.  For each job find the last job that ends <= its start.
    # ---------------------------------------------------------------------
    # ``bisect_right`` returns the insertion point to keep ``ends`` sorted.
    # The predecessor index is that point minus one.
    p = [bisect_right(ends, starts[i]) - 1 for i in range(n)]

    # ---------------------------------------------------------------------
    # 3.  DP arrays: dp[i] = best weight using jobs[0..i]
    # ---------------------------------------------------------------------
    dp = [0.0] * (n + 1)  # dp[0] = 0 for convenience
    for i in range(1, n + 1):
        # Option 1: skip current job
        skip = dp[i - 1]
        # Option 2: take current job
        take = weights[i - 1] + dp[p[i - 1] + 1]
        dp[i] = skip if skip >= take else take

    total_weight = dp[n]

    # ---------------------------------------------------------------------
    # 4.  Reconstruct one optimal set of jobs.
    # ---------------------------------------------------------------------
    chosen = []
    i = n
    while i > 0:
        if dp[i] == weights[i - 1] + dp[p[i - 1] + 1]:
            chosen.append(orig_indices[i - 1])
            i = p[i - 1] + 1
        else:
            i -= 1

    # ``chosen`` is in reverse order of end times; we need it sorted by start
    # time (and index for ties).  ``jobs`` contains the original tuples.
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return total_weight, chosen

# ---------------------------------------------------------------------------
# End of module
# ---------------------------------------------------------------------------
""
