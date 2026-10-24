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

    for pos in range(n):
        idx = order[pos]
        s, _, w = jobs[idx]
        # number of jobs (in end order) with end <= s
        p = bisect_right(ends, s, 0, pos)
        prev[pos] = p
        with_job = dp[p] + w
        without = dp[pos]
        if with_job > without:
            dp[pos + 1] = with_job
            take[pos] = True
        else:
            dp[pos + 1] = without

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
