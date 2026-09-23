def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort job indices by end time, then start time, then index for stability
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))

    ends = [jobs[i][1] for i in order]

    # dp[k] = best weight using first k jobs in sorted order
    dp = [0.0] * (n + 1)

    # prev[k] = index in sorted order of the last job compatible with job at sorted pos k (1-based)
    # Instead compute via binary search on the fly for each job

    import bisect

    for k in range(1, n + 1):
        idx = order[k - 1]
        s, e, w = jobs[idx]
        # Find latest job in sorted order (1-based) that ends <= s
        p = bisect.bisect_right(ends, s, 0, k - 1)
        take = w + dp[p]
        skip = dp[k - 1]
        dp[k] = take if take > skip else skip

    # Reconstruct one optimal solution
    chosen = []
    k = n
    while k > 0:
        idx = order[k - 1]
        s, e, w = jobs[idx]
        p = bisect.bisect_right(ends, s, 0, k - 1)
        take = w + dp[p]
        if take > dp[k - 1]:
            chosen.append(idx)
            k = p
        else:
            k -= 1

    # Sort chosen indices by (start, index)
    chosen.sort(key=lambda i: (jobs[i][0], i))

    return (dp[n], chosen)
