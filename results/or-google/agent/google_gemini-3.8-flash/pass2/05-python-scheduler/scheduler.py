import bisect


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    if not jobs:
        return 0.0, []

    n = len(jobs)
    # Sort jobs by end time, keeping original index
    sorted_jobs = sorted(enumerate(jobs), key=lambda item: item[1][1])
    ends = [job[1] for _, job in sorted_jobs]

    dp = [0.0] * (n + 1)
    prev = [0] * (n + 1)
    take = [False] * (n + 1)

    for i in range(1, n + 1):
        orig_idx, (start, end, weight) = sorted_jobs[i - 1]
        p = bisect.bisect_right(ends, start)
        prev[i] = p
        take_weight = weight + dp[p]
        if take_weight > dp[i - 1]:
            dp[i] = take_weight
            take[i] = True
        else:
            dp[i] = dp[i - 1]

    # Reconstruct chosen jobs
    chosen = []
    curr = n
    while curr > 0:
        if take[curr]:
            chosen.append(sorted_jobs[curr - 1][0])
            curr = prev[curr]
        else:
            curr -= 1

    chosen.sort(key=lambda idx: (jobs[idx][0], idx))
    return float(dp[n]), chosen
