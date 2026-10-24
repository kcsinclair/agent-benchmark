from bisect import bisect_right


def best_schedule(jobs):
    n = len(jobs)
    if n == 0:
        return (0.0, [])
    order = sorted(range(n), key=lambda i: jobs[i][1])
    ends = [jobs[i][1] for i in order]
    dp = [0.0] * (n + 1)
    prev = [0] * n
    take = [False] * n
    for k in range(n):
        s, _, w = jobs[order[k]]
        p = bisect_right(ends, s)
        prev[k] = p
        cand = dp[p] + w
        if cand > dp[k]:
            dp[k + 1] = cand
            take[k] = True
        else:
            dp[k + 1] = dp[k]
    chosen = []
    k = n
    while k > 0:
        if take[k - 1]:
            chosen.append(order[k - 1])
            k = prev[k - 1]
        else:
            k -= 1
    chosen.sort(key=lambda i: (jobs[i][0], i))
    return (float(dp[n]), chosen)
