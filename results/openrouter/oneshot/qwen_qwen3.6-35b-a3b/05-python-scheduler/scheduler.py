def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Weighted Interval Scheduling.
    
    Args:
        jobs: list of (start, end, weight) tuples
        
    Returns:
        (total_weight, chosen_indices) where chosen_indices are sorted by start time
        (ties broken by index ascending)
    """
    if not jobs:
        return (0.0, [])
    
    n = len(jobs)
    
    # Create a list of (start, end, weight, original_index)
    indexed_jobs = [(jobs[i][0], jobs[i][1], jobs[i][2], i) for i in range(n)]
    
    # Sort by end time. If end times are equal, sort by start time, then by index.
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    # After sorting, we need to find for each job the latest job that doesn't overlap with it.
    # Two jobs don't overlap if one ends <= the other starts (touching is allowed).
    # For job i (in sorted order), we want the latest job j < i such that jobs[j].end <= jobs[i].start.
    
    # Extract end times for binary search
    end_times = [job[1] for job in indexed_jobs]
    
    # Precompute p[i] = the index in the sorted array of the latest non-overlapping job before i
    # p[i] = largest j < i such that indexed_jobs[j].end <= indexed_jobs[i].start
    # If no such j exists, p[i] = -1
    
    import bisect
    
    p = [-1] * n
    for i in range(n):
        start_i = indexed_jobs[i][0]
        # Find the rightmost job with end_time <= start_i
        # bisect_right returns the insertion point after all elements <= start_i
        # So bisect_right(end_times, start_i) gives us the count of elements <= start_i
        # The index of the last such element is bisect_right(...) - 1
        idx = bisect.bisect_right(end_times, start_i) - 1
        if idx >= 0:
            p[i] = idx
        else:
            p[i] = -1
    
    # DP: dp[i] = maximum weight using a subset of the first i+1 jobs (indexed_jobs[0..i])
    # dp[i] = max(dp[i-1], weight[i] + dp[p[i]]) if p[i] != -1
    # dp[i] = max(dp[i-1], weight[i]) if p[i] == -1
    
    dp = [0.0] * n
    
    dp[0] = indexed_jobs[0][2]
    
    for i in range(1, n):
        # Option 1: don't include job i
        exclude = dp[i - 1]
        
        # Option 2: include job i
        include = indexed_jobs[i][2]
        if p[i] != -1:
            include += dp[p[i]]
        
        dp[i] = max(exclude, include)
    
    total_weight = dp[n - 1]
    
    # Reconstruct the solution
    chosen_indices = []
    i = n - 1
    while i >= 0:
        # Check if job i was included
        include_val = indexed_jobs[i][2]
        if p[i] != -1:
            include_val += dp[p[i]]
        
        if i > 0 and dp[i - 1] >= include_val:
            # Job i was not included (or including it gives same or less weight)
            i -= 1
        else:
            # Job i was included
            chosen_indices.append(indexed_jobs[i][3])
            if p[i] != -1:
                i = p[i]
            else:
                i = -1
    
    # Sort chosen indices by start time, breaking ties by index ascending
    # We need to get the start time for each chosen index
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (total_weight, chosen_indices)
