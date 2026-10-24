# scheduler.py
from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Weighted interval scheduling.

    Returns (max_total_weight, chosen_indices), where chosen_indices refer to the
    input list and are sorted by job start time (ties broken by index ascending).
    Jobs that merely touch (one ends where another starts) are compatible.
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Order jobs by end time (stable, so original index order is preserved on ties).
    order = sorted(range(n), key=lambda i: jobs[i][1])
    ends = [jobs[i][1] for i in order]

    # dp[k] = best total weight using only the first k jobs in end-sorted order.
    # take[k] = True if the optimum for prefix k includes job order[k-1].
    # prev[k] = number of jobs (prefix length) compatible with order[k-1],
    #           i.e., the largest j such that ends[j-1] <= start of order[k-1].
    dp = [0.0] * (n + 1)
    take = [False] * (n + 1)
    prev = [0] * (n + 1)

    for k in range(1, n + 1):
        i = order[k - 1]
        start, _, weight = jobs[i]
        # Number of end-sorted jobs whose end <= start (touching allowed).
        p = bisect_right(ends, start, 0, k - 1)
        prev[k] = p
        with_job = dp[p] + weight
        without_job = dp[k - 1]
        if with_job > without_job:
            dp[k] = with_job
            take[k] = True
        else:
            dp[k] = without_job
            take[k] = False

    # Reconstruct the chosen set iteratively.
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
