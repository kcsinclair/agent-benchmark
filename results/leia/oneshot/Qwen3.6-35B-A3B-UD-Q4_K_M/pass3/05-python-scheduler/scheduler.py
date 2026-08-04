def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solve the weighted interval scheduling problem in O(n log n) time.
    
    Args:
        jobs: list of (start, end, weight) tuples
        
    Returns:
        (total_weight, chosen_indices) where chosen_indices are sorted by start time
        (ties broken by index ascending)
    """
    if not jobs:
        return (0.0, [])
    
    n = len(jobs)
    
    # Create indexed jobs: (start, end, weight, original_index)
    indexed_jobs = [(jobs[i][0], jobs[i][1], jobs[i][2], i) for i in range(n)]
    
    # Sort by end time. If end times are equal, sort by start time, then by index
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    # Extract sorted arrays
    ends = [job[1] for job in indexed_jobs]
    starts = [job[0] for job in indexed_jobs]
    weights = [job[2] for job in indexed_jobs]
    orig_indices = [job[3] for job in indexed_jobs]
    
    # For each job i, find the largest j < i such that ends[j] <= starts[i]
    # This is the latest non-overlapping job that can be scheduled before job i
    # We use binary search on the ends array
    
    def find_p(i: int) -> int:
        """Find the largest index j < i such that ends[j] <= starts[i]. Return -1 if none exists."""
        target = starts[i]
        # Binary search in ends[0..i-1] for the rightmost value <= target
        lo, hi = 0, i - 1
        result = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if ends[mid] <= target:
                result = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return result
    
    # DP: dp[i] = maximum weight using a subset of jobs indexed_jobs[0..i]
    # dp[i] = max(dp[i-1], weights[i] + dp[p(i)]) if p(i) != -1, else max(dp[i-1], weights[i])
    
    dp = [0.0] * n
    dp[0] = weights[0]
    
    for i in range(1, n):
        p = find_p(i)
        include_weight = weights[i]
        if p != -1:
            include_weight += dp[p]
        exclude_weight = dp[i - 1]
        dp[i] = max(include_weight, exclude_weight)
    
    total_weight = dp[n - 1]
    
    # Backtrack to find which jobs were chosen
    chosen = []
    i = n - 1
    while i >= 0:
        p = find_p(i)
        include_weight = weights[i]
        if p != -1:
            include_weight += dp[p]
        
        if include_weight >= dp[i - 1] if i > 0 else include_weight >= 0:
            # Job i is included
            chosen.append(orig_indices[i])
            i = p
        else:
            # Job i is not included
            i -= 1
    
    # Sort chosen indices by start time (using the original job data), ties by index ascending
    # We need to sort by (start_time, original_index)
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (total_weight, chosen)
