from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """Weighted interval scheduling in O(n log n).

    jobs: list of (start, end, weight).
    Returns (max_total_weight, sorted list of chosen indices into jobs).
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort jobs by end time; keep original indices.
    order = sorted(range(n), key=lambda i: (jobs[i][1], i))

    ends = [jobs[i][1] for i in order]

    # dp[k]: best total weight using the first k jobs in sorted order.
    # prev[k]: index in sorted order of the previous compatible job (0-based,
    #          or -1 if none), for reconstruction.
    dp = [0.0] * (n + 1)
    prev = [-1] * (n + 1)

    for k in range(1, n + 1):
        idx = order[k - 1]
        start = jobs[idx][0]
        weight = jobs[idx][2]

        # p = number of jobs (among first k-1 sorted) whose end <= start
        p = bisect_right(ends, start, 0, k - 1)

        take = weight + dp[p]
        if take > dp[k - 1]:
            dp[k] = take
            prev[k] = p
        else:
            dp[k] = dp[k - 1]
            prev[k] = k - 1

    # Reconstruct chosen indices.
    chosen = []
    k = n
    while k > 0:
        if prev[k] == k - 1:
            k -= 1
        else:
            chosen.append(order[k - 1])
            k = prev[k]

    # Sort chosen indices by (start, index) as required.
    chosen.sort(key=lambda i: (jobs[i][0], i))

    return (dp[n], chosen)
