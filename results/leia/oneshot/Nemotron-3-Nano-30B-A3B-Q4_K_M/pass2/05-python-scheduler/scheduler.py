import bisect

def best_schedule(jobs):
    n = len(jobs)
    if n == 0:
        return (0.0, [])
    
    sorted_jobs = sorted(enumerate(jobs), key=lambda x: x[1][1])
    starts = [job[0] for job in sorted_jobs]
    ends = [job[1][1] for job in sorted_jobs]
    weights = [job[1][2] for job in sorted_jobs]
    
    dp = [0.0] * n
    prev = [-1] * n
    dp[0] = weights[0]
    
    for i in range(1, n):
        s = starts[i]
        pos = bisect.bisect_right(ends, s) - 1
        if pos >= 0:
            dp[i] = dp[pos] + weights[i]
            prev[i] = pos
        else:
            dp[i] = weights[i]
        
        if dp[i-1] > dp[i]:
            dp[i] = dp[i-1]
            prev[i] = -1
    
    max_weight = dp[-1]
    current = n - 1
    chosen = []
    while current != -1:
        chosen.append(sorted_jobs[current][0])
        current = prev[current]
    
    chosen.sort(key=lambda idx: (starts[idx], idx))
    
    return (float(max_weight), chosen)
