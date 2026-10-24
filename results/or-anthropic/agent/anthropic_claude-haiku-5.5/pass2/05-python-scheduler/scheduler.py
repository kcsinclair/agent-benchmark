from bisect import bisect_right


def best_schedule(jobs):
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort job indices by end time (ties by start, then index for determinism).
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))
    ends = [jobs[i][1] for i in order]

    # p[k] = number of sorted jobs (among the first k) that end <= start of job order[k-1]
    # Using 1-based DP: dp[k] = best total using first k jobs in end-sorted order.
    dp = [0.0] * (n + 1)
    take = [False] * (n + 1)
    prev = [0] * (n + 1)

    for k in range(1, n + 1):
        idx = order[k - 1]
        start, _, w = jobs[idx]
        # number of jobs (in sorted order) with end <= start; all such are before k
        p = bisect_right(ends, start, 0, k - 1)
        with_job = w + dp[p]
        if with_job > dp[k - 1]:
            dp[k] = with_job
            take[k] = True
            prev[k] = p
        else:
            dp[k] = dp[k - 1]
            take[k] = False

    # Reconstruct chosen jobs iteratively.
    chosen = []
    k = n
    while k > 0:
        if take[k]:
            chosen.append(order[k - 1])
            k = prev[k]
        else:
            k -= 1

    chosen.sort(key=lambda i: (jobs[i][0], i))
    return (float(dp[n]), chosen)
