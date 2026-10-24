# scheduler.py
from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort job indices by end time.
    order = sorted(range(n), key=lambda i: jobs[i][1])
    ends = [jobs[i][1] for i in order]

    dp = [0.0] * (n + 1)
    prev = [0] * (n + 1)       # prev[k] = number of sorted jobs compatible with k-th job
    take = [False] * (n + 1)

    for k in range(1, n + 1):
        s, e, w = jobs[order[k - 1]]
        # Count of jobs whose end <= s (touching allowed). Since s < e, all of
        # these come before position k in the sorted order.
        p = bisect_right(ends, s, 0, k - 1)
        prev[k] = p
        with_job = dp[p] + w
        without = dp[k - 1]
        if with_job > without:
            dp[k] = with_job
            take[k] = True
        else:
            dp[k] = without

    # Iterative reconstruction.
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
