from bisect import bisect_right


def best_schedule(jobs):
    """Weighted interval scheduling in O(n log n).

    jobs: list of (start, end, weight). Touching intervals are compatible.
    Returns (total_weight, chosen_indices) with indices sorted by start
    (ties broken by index ascending).
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort job indices by end time (stable, so ties keep input order).
    order = sorted(range(n), key=lambda i: (jobs[i][1], i))
    ends = [jobs[i][1] for i in order]

    # p[k] = number of sorted jobs (among first k positions) whose end <= start
    # of the k-th sorted job. Since sorted by end, these are a prefix.
    p = [0] * n
    for k in range(n):
        s = jobs[order[k]][0]
        # count of jobs with end <= s; only need among positions < k, but
        # any job with end <= s < end_k automatically has position < k.
        p[k] = bisect_right(ends, s)

    # dp[k] = best weight using the first k sorted jobs.
    dp = [0.0] * (n + 1)
    take = [False] * (n + 1)
    for k in range(1, n + 1):
        w = jobs[order[k - 1]][2]
        with_job = w + dp[p[k - 1]]
        without = dp[k - 1]
        if with_job > without:
            dp[k] = with_job
            take[k] = True
        else:
            dp[k] = without

    # Backtrack.
    chosen = []
    k = n
    while k > 0:
        if take[k]:
            idx = order[k - 1]
            chosen.append(idx)
            k = p[k - 1]
        else:
            k -= 1

    chosen.sort(key=lambda i: (jobs[i][0], i))
    return (float(dp[n]), chosen)
