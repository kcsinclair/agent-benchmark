import bisect

def best_schedule(jobs):
    if not jobs:
        return (0.0, [])
    
    n = len(jobs)
    sorted_jobs = sorted(enumerate(jobs), key=lambda x: x[1][1])
    starts = [job[1][0] for job in sorted_jobs]
    ends = [job[1][1] for job in sorted_jobs]
    weights = [job[1][2] for job in sorted_jobs]
    
    dp = [0.0] * n
    dp[0] = weights[0]
    
    for i in range(1, n):
        current_start = starts[i]
        pos = bisect.bisect_right(ends, current_start)
        j = pos - 1
        include_weight = weights[i]
        if j >= 0:
            include_weight += dp[j]
        dp[i] = max(dp[i-1], include_weight)
    
    total_weight = dp[-1]
    current = n - 1
    chosen_indices = []
    
    while current >= 0:
        if current == 0:
            if dp[current] == weights[current]:
                chosen_indices.append(sorted_jobs[current][0])
            break
        else:
            if dp[current] == dp[current-1]:
                current -= 1
            else:
                j = bisect.bisect_right(ends, starts[current]) - 1
                if j >= 0:
                    current = j
                else:
                    current = -1
                chosen_indices.append(sorted_jobs[current + 1][0])
    
    chosen_indices.sort(key=lambda idx: starts[idx])
    return (total_weight, chosen_indices)
