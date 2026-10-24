"""Weighted interval scheduling in O(n log n)."""
from bisect import bisect_right


def best_schedule(jobs):
    n = len(jobs)
    if n == 0:
        return (0.0, [])
    order = sorted(range(n), key=lambda i: jobs[i][1])
    ends = [jobs[i][1] for i in order]
    dp = [0.0] * (n + 1)
    pred = [0] * (n + 1)
    take = [False] * (n + 1)
    for j in range(1, n + 1):
        s, _, w = jobs[order[j - 1]]
        p = bisect_right(ends, s, 0, j - 1)
        pred[j] = p
        cand = dp[p] + float(w)
        if cand > dp[j - 1]:
            dp[j] = cand
            take[j] = True
        else:
            dp[j] = dp[j - 1]
    chosen = []
    j = n
    while j > 0:
        if take[j]:
            chosen.append(order[j - 1])
            j = pred[j]
        else:
            j -= 1
    chosen.sort(key=lambda i: (jobs[i][0], i))
    return (float(dp[n]), chosen)
