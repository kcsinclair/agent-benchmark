"""Weighted interval scheduling, O(n log n)."""

from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort jobs by end time (tie-break by index for determinism).
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))

    ends = [jobs[i][1] for i in order]
    starts = [jobs[i][0] for i in order]

    # p[k] = number of jobs (in sorted order) whose end <= starts[k].
    # Using bisect_right on ends with key = starts[k] gives exactly that count
    # because ties (end == start) are allowed.
    p = [bisect_right(ends, starts[k], 0, k) - 1 for k in range(n)]

    # dp[k] = best total weight considering jobs order[0..k].
    dp = [0.0] * (n + 1)
    take = [False] * n  # whether sorted job k is chosen in the optimal for prefix k

    for k in range(n):
        w = jobs[order[k]][2]
        with_k = w + dp[p[k] + 1]
        without_k = dp[k]
        if with_k > without_k:
            dp[k + 1] = with_k
            take[k] = True
        else:
            dp[k + 1] = without_k

    # Reconstruct chosen indices (iterative).
    chosen = []
    k = n - 1
    while k >= 0:
        if take[k]:
            chosen.append(order[k])
            k = p[k]
        else:
            k -= 1

    # Sort chosen indices by start time, tie-break by index ascending.
    chosen.sort(key=lambda i: (jobs[i][0], i))

    return (dp[n], chosen)
