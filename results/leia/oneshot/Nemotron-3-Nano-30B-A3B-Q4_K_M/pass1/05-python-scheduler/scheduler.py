import bisect

def best_schedule(jobs):
    n = len(jobs)
    if n == 0:
        return (0.0, [])
    
    sorted_jobs = sorted(enumerate(jobs), key=lambda x: x[1][1])
    starts = [job[1][0] for _, job in sorted_jobs]
    ends = [job[1][1] for _, job in sorted_jobs]
    weights = [job[1][2] for _, job in sorted_jobs]
    orig_indices = [idx for idx, _ in sorted_jobs]
    
    dp = [0.0] * n
    dp[0] = weights[0]
    max_dp = [0.0] * n
    max_dp[0] = dp[0]
    
    for i in range(1, n):
        s = starts[i]
        pos = bisect.bisect_right(ends, s) - 1
        if pos >= 0:
            prev_max = max_dp[pos]
        else:
            prev_max = 0.0
        dp[i] = weights[i] + prev_max
        max_dp[i] = max(max_dp[i-1], dp[i])
    
    max_weight = max_dp[-1]
    
    i = n - 1
    chosen_sorted = []
    while i >= 0:
        if dp[i] == max_dp[i] and (i == 0 or dp[i] > dp[i-1]):
            chosen_sorted.append(orig_indices[i])
            s = starts[i]
            pos = bisect.bisect_right(ends, s) - 1
            i = pos
        else:
            i -= 1
    
    chosen_sorted.sort(key=lambda idx: (starts[idx], idx))
    return (max_weight, chosen_sorted)
