import bisect


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # sort indices by end time
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0]))
    ends_sorted = [jobs[i][1] for i in order]  # sorted ends, aligned with `order`
    starts_sorted_by_end_order = [jobs[i][0] for i in order]

    # dp[k] = best total weight using first k jobs (in end-sorted order)
    dp = [0.0] * (n + 1)
    # choice[k]: True if job order[k-1] is taken in optimal solution for dp[k]
    take = [False] * (n + 1)
    # p[k-1]: index (1-based in dp array) of last compatible job before job order[k-1]
    p = [0] * n

    for k in range(1, n + 1):
        idx = order[k - 1]
        s = jobs[idx][0]
        # find largest j such that ends_sorted[j-1] <= s  (jobs are 1-indexed in dp)
        # ends_sorted is sorted ascending; find rightmost position with end <= s
        j = bisect.bisect_right(ends_sorted, s, 0, k - 1)
        p[k - 1] = j

        w = jobs[idx][2]
        with_job = dp[j] + w
        without_job = dp[k - 1]

        if with_job > without_job:
            dp[k] = with_job
            take[k] = True
        else:
            dp[k] = without_job
            take[k] = False

    total_weight = dp[n]

    chosen = []
    k = n
    while k > 0:
        if take[k]:
            idx = order[k - 1]
            chosen.append(idx)
            k = p[k - 1]
        else:
            k -= 1

    chosen_sorted = sorted(chosen, key=lambda i: (jobs[i][0], i))

    return (float(total_weight), chosen_sorted)
