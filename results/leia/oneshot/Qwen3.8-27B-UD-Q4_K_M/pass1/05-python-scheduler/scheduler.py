def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])
    
    # Create list of (start, end, weight, original_index)
    indexed_jobs = [(jobs[i][0], jobs[i][1], jobs[i][2], i) for i in range(n)]
    
    # Sort by end time, then by start time, then by index for deterministic tie-breaking
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    # Extract sorted arrays
    starts = [x[0] for x in indexed_jobs]
    ends = [x[1] for x in indexed_jobs]
    weights = [x[2] for x in indexed_jobs]
    orig_indices = [x[3] for x in indexed_jobs]
    
    # For each job i (in sorted order), find the rightmost job j such that ends[j] <= starts[i]
    # This is the last job that is compatible with job i
    # We use binary search on the ends array
    import bisect
    
    # dp[i] = max weight using jobs 0..i (inclusive) in sorted order
    # dp[i] = max(dp[i-1], weights[i] + (dp[p(i)] if p(i) >= 0 else 0))
    # where p(i) is the largest index j < i such that ends[j] <= starts[i]
    
    # We'll compute dp iteratively
    # dp[i] represents the best weight considering the first i+1 jobs (indices 0 to i)
    
    # Let's use 1-indexed for clarity: dp[i] = best weight using first i jobs (indices 0 to i-1)
    # dp[0] = 0
    # dp[i] = max(dp[i-1], weights[i-1] + dp[p(i-1)+1]) where p(i-1) is the last compatible job index
    
    # Actually, let me use 0-indexed dp where dp[i] = best weight using jobs 0..i
    # dp[i] = max(dp[i-1], weights[i] + (dp[p(i)] if p(i) >= 0 else 0))
    
    # p(i) = rightmost index j < i such that ends[j] <= starts[i]
    # Since ends is sorted (because we sorted by end time), we can binary search
    
    # Let's precompute p(i) for each i
    # For job i, we want the largest j < i such that ends[j] <= starts[i]
    # Since ends is non-decreasing, we can use bisect_right on ends[0:i] to find the rightmost position where ends[j] <= starts[i]
    
    # Actually, bisect_right(ends, starts[i]) gives the insertion point, so the index would be bisect_right(ends, starts[i]) - 1
    # But we need j < i, so we take min(bisect_right(ends, starts[i]) - 1, i - 1)
    
    # Let's compute dp and also keep track of choices for backtracking
    
    # dp[i] = best weight using jobs 0..i
    # choice[i] = True if we include job i, False otherwise
    
    dp = [0.0] * n
    choice = [False] * n
    
    for i in range(n):
        # Find p(i): rightmost j < i such that ends[j] <= starts[i]
        # Use bisect_right on the ends array up to index i
        # bisect_right(ends, starts[i], 0, i) gives the number of elements in ends[0:i] that are <= starts[i]
        # So the rightmost such index is bisect_right(ends, starts[i], 0, i) - 1
        pos = bisect.bisect_right(ends, starts[i], 0, i)
        p = pos - 1  # This is the rightmost index j < i with ends[j] <= starts[i], or -1 if none
        
        if i == 0:
            dp[i] = weights[i]
            choice[i] = True
        else:
            # Option 1: don't include job i
            opt1 = dp[i - 1]
            # Option 2: include job i
            opt2 = weights[i] + (dp[p] if p >= 0 else 0.0)
            
            if opt2 > opt1:
                dp[i] = opt2
                choice[i] = True
            else:
                dp[i] = opt1
                choice[i] = False
    
    total_weight = dp[n - 1]
    
    # Backtrack to find chosen indices
    chosen = []
    i = n - 1
    while i >= 0:
        if choice[i]:
            chosen.append(orig_indices[i])
            # Find p(i) again
            pos = bisect.bisect_right(ends, starts[i], 0, i)
            p = pos - 1
            i = p
        else:
            i -= 1
    
    # Sort chosen indices by start time, then by original index
    # We need to sort by (start, original_index)
    # Map original index to (start, original_index)
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (total_weight, chosen)
