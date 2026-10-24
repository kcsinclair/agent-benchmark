"""Weighted interval scheduling in O(n log n) time.

Usage:
    from scheduler import best_schedule
"""

from bisect import bisect_right


def best_schedule(jobs):
    """Return (total_weight, chosen_indices) for a maximum-weight set of
    non-overlapping jobs. Jobs that touch (one ends at t, the next starts
    at t) are compatible. The indices are sorted by start time, then by
    index."""
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort job indices by end time (ties broken by index).
    order = sorted(range(n), key=lambda i: (jobs[i][1], i))
    ends = [jobs[i][1] for i in order]

    # p[k] = number of sorted jobs (among the first k) whose end <= start of
    # sorted job k. Those are exactly the jobs compatible with job k.
    # dp[k] = best total weight using only the first k sorted jobs.
    dp = [0.0] * (n + 1)
    p = [0] * n
    take = [False] * n

    for k in range(n):
        s, _, w = jobs[order[k]]
        # Every job with end <= s comes before k in end order, since
        # end_k > s. The hi=k bound is only a safeguard.
        pk = bisect_right(ends, s, 0, k)
        p[k] = pk
        with_job = w + dp[pk]
        without = dp[k]
        if with_job > without:
            dp[k + 1] = with_job
            take[k] = True
        else:
            dp[k + 1] = without

    # Iterative reconstruction, so no recursion limit issues.
    chosen = []
    k = n - 1
    while k >= 0:
        if take[k]:
            chosen.append(order[k])
            k = p[k] - 1
        else:
            k -= 1

    chosen.sort(key=lambda i: (jobs[i][0], i))
    return (float(dp[n]), chosen)
