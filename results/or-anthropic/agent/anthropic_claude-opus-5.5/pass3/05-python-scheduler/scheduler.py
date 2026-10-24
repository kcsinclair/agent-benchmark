"""Weighted interval scheduling in O(n log n)."""
from bisect import bisect_right


def best_schedule(jobs):
    n = len(jobs)
    if n == 0:
        return (0.0, [])
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))
    ends = [jobs[i][1] for i in order]
    # p[k] = number of jobs (in sorted order) with end <= start of job order[k]
    dp = [0.0] * (n + 1)
    take = [False] * n
    p = [0] * n
    for k in range(n):
        s, _, w = jobs[order[k]]
        j = bisect_right(ends, s, 0, k)
        p[k] = j
        incl = dp[j] + w
        if incl > dp[k]:
            dp[k + 1] = incl
            take[k] = True
        else:
            dp[k + 1] = dp[k]
    chosen = []
    k = n
    while k > 0:
        if take[k - 1]:
            chosen.append(order[k - 1])
            k = p[k - 1]
        else:
            k -= 1
    chosen.sort(key=lambda i: (jobs[i][0], i))
    return (float(dp[n]), chosen)
