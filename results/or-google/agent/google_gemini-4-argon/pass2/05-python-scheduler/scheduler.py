from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort jobs by end time, then start time, then original index
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))
    ends = [jobs[i][1] for i in order]

    # dp[k] stores the maximum weight using a subset of the first k sorted jobs (1-indexed)
    dp = [0.0] * (n + 1)
    prev = [0] * (n + 1)
    take = [False] * (n + 1)

    for k in range(1, n + 1):
        idx = order[k - 1]
        start, _, weight = jobs[idx]

        # Find how many sorted jobs have end_time <= start
        p = bisect_right(ends, start, 0, k - 1)
        prev[k] = p

        cand = dp[p] + weight
        if cand > dp[k - 1]:
            dp[k] = cand
            take[k] = True
        else:
            dp[k] = dp[k - 1]

    # Reconstruct optimal subset iteratively
    chosen: list[int] = []
    k = n
    while k > 0:
        if take[k]:
            chosen.append(order[k - 1])
            k = prev[k]
        else:
            k -= 1

    chosen.sort(key=lambda i: (jobs[i][0], i))
    return (float(dp[n]), chosen)
