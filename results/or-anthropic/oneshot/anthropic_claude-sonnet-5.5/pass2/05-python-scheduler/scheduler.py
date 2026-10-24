from bisect import bisect_right


def best_schedule(jobs):
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    order = sorted(range(n), key=lambda i: jobs[i][1])
    ends = [jobs[i][1] for i in order]

    dp = [0.0] * (n + 1)
    take = [False] * n
    prev = [0] * n

    for k in range(n):
        s, _, w = jobs[order[k]]
        p = bisect_right(ends, s, 0, k)  # jobs with end <= s (all lie before k)
        prev[k] = p
        cand = dp[p] + w
        if cand > dp[k]:
            dp[k + 1] = cand
            take[k] = True
        else:
            dp[k + 1] = dp[k]

    chosen = []
    i = n
    while i > 0:
        if take[i - 1]:
            chosen.append(order[i - 1])
            i = prev[i - 1]
        else:
            i -= 1

    chosen.sort(key=lambda j: (jobs[j][0], j))
    return (float(dp[n]), chosen)
