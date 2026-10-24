# scheduler.py
"""Weighted interval scheduling in O(n log n).

Approach: sort jobs by end time. Let dp[i] be the best total weight using
only the first i jobs in end-time order. For job i (in sorted order), either
skip it (dp[i-1]) or take it, which adds its weight to the best solution
among jobs ending at or before its start. That predecessor boundary is found
by binary search over the sorted end times (bisect_right, so a job ending
exactly at this job's start is compatible — touching is allowed).

Reconstruction walks backward through the decision table, so no recursion
is used anywhere.
"""

from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return 0.0, []

    # Order job indices by end time (ties by start, then index, for determinism).
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))
    ends = [jobs[i][1] for i in order]

    # pred[k] = number of sorted jobs (among the first k in end order) that end
    # no later than the start of the k-th job; i.e., the largest compatible prefix.
    # dp[k] = best weight using the first k jobs in end order (dp[0] = 0).
    dp = [0.0] * (n + 1)
    take = [False] * (n + 1)   # whether job k (1-based) was taken in dp[k]
    pred = [0] * (n + 1)

    for k in range(1, n + 1):
        idx = order[k - 1]
        start, _end, weight = jobs[idx]
        p = bisect_right(ends, start, 0, k - 1)  # jobs with end <= start
        pred[k] = p
        with_job = dp[p] + weight
        if with_job > dp[k - 1]:
            dp[k] = with_job
            take[k] = True
        else:
            dp[k] = dp[k - 1]
            take[k] = False

    # Reconstruct the chosen set iteratively.
    chosen = []
    k = n
    while k > 0:
        if take[k]:
            chosen.append(order[k - 1])
            k = pred[k]
        else:
            k -= 1

    chosen.sort(key=lambda i: (jobs[i][0], i))
    return dp[n], chosen
