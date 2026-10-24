"""Weighted interval scheduling in O(n log n) time.

Importing this module has no side effects. It uses only the standard library.
"""

from bisect import bisect_right


def best_schedule(jobs):
    """Return (total_weight, chosen_indices) for a maximum-weight set of
    non-overlapping jobs.

    jobs: list of (start, end, weight). Touching jobs (one ends at t, the
    next starts at t) are compatible.

    chosen_indices are indices into the input list, sorted by start time,
    with ties broken by index ascending.
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort job indices by end time. Start time and index only make the order
    # deterministic.
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))
    ends = [jobs[i][1] for i in order]

    # dp[k] = best total weight using only the first k jobs in sorted order.
    dp = [0.0] * (n + 1)
    # prev[k] = number of jobs among the first k (sorted) whose end <= start
    # of job k.
    prev = [0] * n
    # take[k] = True if the optimum for dp[k+1] includes sorted job k.
    take = [False] * n

    for k in range(n):
        s, e, w = jobs[order[k]]
        # Every job before k with end <= s is compatible with job k. Job k
        # itself has end > s, so searching in [0, k) is enough.
        p = bisect_right(ends, s, 0, k)
        prev[k] = p
        with_k = dp[p] + float(w)
        without_k = dp[k]
        if with_k > without_k:
            dp[k + 1] = with_k
            take[k] = True
        else:
            dp[k + 1] = without_k

    # Rebuild the chosen set by walking backwards (iterative, no recursion).
    chosen = []
    k = n
    while k > 0:
        if take[k - 1]:
            chosen.append(order[k - 1])
            k = prev[k - 1]
        else:
            k -= 1

    chosen.sort(key=lambda i: (jobs[i][0], i))

    # Re-add the chosen weights in start order, so the returned total matches
    # the sum a checker would compute.
    total = 0.0
    for i in chosen:
        total += float(jobs[i][2])

    return (total, chosen)
