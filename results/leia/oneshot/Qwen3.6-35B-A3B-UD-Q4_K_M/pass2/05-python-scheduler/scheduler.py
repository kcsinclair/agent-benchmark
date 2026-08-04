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
    
    # Sort by end time. For ties in end time, we can break ties arbitrarily for DP,
    # but we need to be careful with the p[j] computation.
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    # Extract sorted arrays
    ends = [job[1] for job in indexed_jobs]
    starts = [job[0] for job in indexed_jobs]
    weights = [job[2] for job in indexed_jobs]
    orig_indices = [job[3] for job in indexed_jobs]
    
    # For each job j, find the largest index i < j such that ends[i] <= starts[j]
    # This is the "previous compatible job" using binary search.
    # Since ends is sorted, we can use bisect_right on ends to find the rightmost position
    # where end <= starts[j], then subtract 1 to get the index.
    
    import bisect
    
    # p[j] = index of the latest job that doesn't overlap with job j (i.e., ends[i] <= starts[j])
    # If no such job exists, p[j] = -1
    p = [-1] * n
    for j in range(n):
        # Find the rightmost index i such that ends[i] <= starts[j]
        # bisect_right returns the insertion point after all elements <= starts[j]
        # So the element at position (pos - 1) is the largest index with end <= starts[j]
        pos = bisect.bisect_right(ends, starts[j])
        if pos > 0:
            p[j] = pos - 1
        else:
            p[j] = -1
    
    # DP: dp[j] = maximum weight using a subset of jobs[0..j]
    # dp[j] = max(dp[j-1], weights[j] + dp[p[j]]) if p[j] != -1 else max(dp[j-1], weights[j])
    # Base case: dp[-1] = 0 (no jobs)
    
    dp = [0.0] * n
    
    # Iterative DP
    for j in range(n):
        # Option 1: don't include job j
        include_prev = dp[j - 1] if j > 0 else 0.0
        
        # Option 2: include job j
        if p[j] == -1:
            include_current = weights[j]
        else:
            include_current = weights[j] + dp[p[j]]
        
        dp[j] = max(include_prev, include_current)
    
    total_weight = dp[n - 1]
    
    # Backtrack to find which jobs were chosen
    chosen = []
    j = n - 1
    while j >= 0:
        # Check if job j was included
        if p[j] == -1:
            include_current = weights[j]
        else:
            include_current = weights[j] + dp[p[j]]
        
        include_prev = dp[j - 1] if j > 0 else 0.0
        
        if include_current >= include_prev:
            # Job j was included (or at least, including it is at least as good)
            chosen.append(orig_indices[j])
            j = p[j]
        else:
            j -= 1
    
    # Sort chosen indices by start time, breaking ties by index ascending
    # We need to get the start time for each chosen job
    chosen_with_start = []
    for idx in chosen:
        chosen_with_start.append((jobs[idx][0], idx))
    
    chosen_with_start.sort(key=lambda x: (x[0], x[1]))
    chosen_indices = [item[1] for item in chosen_with_start]
    
    return (total_weight, chosen_indices)
