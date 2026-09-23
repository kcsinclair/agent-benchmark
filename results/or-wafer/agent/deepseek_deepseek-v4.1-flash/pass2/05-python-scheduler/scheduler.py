"""Weighted interval scheduling, O(n log n).

Choose a max-weight subset of non-overlapping jobs (touching allowed).
"""

from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort jobs by end time; keep original indices.
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))
    ends = [jobs[i][1] for i in order]

    # p[k] = index (in sorted order) of rightmost job compatible with job k,
    # i.e. the largest j < k with ends[j] <= starts[k]; -1 if none.
    p = [0] * n
    for k in range(n):
        start_k = jobs[order[k]][0]
        p[k] = bisect_right(ends, start_k, 0, k) - 1

    # Iterative DP over jobs sorted by end time.
    dp = [0.0] * (n + 1)  # dp[k] = best weight using first k sorted jobs
    for k in range(1, n + 1):
        w = jobs[order[k - 1]][2]
        take = dp[p[k - 1] + 1] + w
        skip = dp[k - 1]
        dp[k] = take if take > skip else skip

    # Reconstruct chosen set.
    chosen = []
    k = n
    while k > 0:
        idx = order[k - 1]
        w = jobs[idx][2]
        take = dp[p[k - 1] + 1] + w
        if take > dp[k - 1]:
            chosen.append(idx)
            k = p[k - 1] + 1
        else:
            k -= 1

    # Sort chosen indices by start time, ties broken by index ascending.
    chosen.sort(key=lambda i: (jobs[i][0], i))
    return (dp[n], chosen)
