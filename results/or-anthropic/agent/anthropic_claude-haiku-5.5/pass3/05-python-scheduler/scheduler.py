from bisect import bisect_right


def best_schedule(jobs):
    """Weighted interval scheduling in O(n log n).

    jobs: list of (start, end, weight). Touching intervals are compatible.
    Returns (total_weight, chosen_indices) with indices sorted by start time
    (ties broken by index ascending).
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort job indices by end time (iterative, no recursion).
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))
    ends = [jobs[i][1] for i in order]

    # p[k] = number of sorted jobs whose end <= start of sorted job k.
    # Since sorted by end, those jobs form a prefix of length p[k].
    p = [0] * n
    for k in range(n):
        s = jobs[order[k]][0]
        # Only jobs with index < k can have end <= s < end_k, so cap at k.
        j = bisect_right(ends, s, 0, k)
        p[k] = j

    # dp[k] = best total using the first k sorted jobs (dp[0] = 0).
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

    # Reconstruct.
    chosen = []
    k = n
    while k > 0:
        if take[k]:
            chosen.append(order[k - 1])
            k = p[k - 1]
        else:
            k -= 1

    chosen.sort(key=lambda i: (jobs[i][0], i))
    return (float(dp[n]), chosen)
