def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])
    
    # Create list of (start, end, weight, original_index)
    indexed_jobs = [(jobs[i][0], jobs[i][1], jobs[i][2], i) for i in range(n)]
    
    # Sort by end time, then by start time, then by index for stability
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    # Extract sorted arrays
    starts = [x[0] for x in indexed_jobs]
    ends = [x[1] for x in indexed_jobs]
    weights = [x[2] for x in indexed_jobs]
    orig_indices = [x[3] for x in indexed_jobs]
    
    # For each job i (in sorted order), find the latest job j < i such that ends[j] <= starts[i]
    # We need to find the rightmost index j in [0, i-1] where ends[j] <= starts[i]
    # Since ends is sorted (because we sorted by end time), we can use binary search.
    
    import bisect
    
    # dp[i] = max weight achievable considering jobs 0..i (in sorted order)
    # dp[i] = max(dp[i-1], weights[i] + dp[p(i)]) where p(i) is the largest index < i with ends[p(i)] <= starts[i]
    # If no such job exists, p(i) = -1, and dp[-1] = 0
    
    # We'll use 1-indexed for convenience: dp[0] = 0, dp[i] for i in 1..n
    # Job i in 1-indexed corresponds to indexed_jobs[i-1]
    
    # For binary search: we want to find the largest index j (0-indexed in the sorted array) such that ends[j] <= starts[i]
    # where i is 0-indexed. Then p(i) in 1-indexed dp terms is j+1 (if j >= 0), else 0.
    
    # Let's precompute p for each job
    # p[i] (0-indexed) = number of jobs with end <= starts[i], i.e., the count of jobs j where ends[j] <= starts[i]
    # Since ends is sorted, we can use bisect_right(ends, starts[i]) to get the count of elements <= starts[i]
    # But we need to be careful: we want the largest index j < i such that ends[j] <= starts[i]
    # Actually, since we're processing in order of increasing end time, and we want compatible jobs,
    # the standard approach is:
    # p(i) = largest index j < i such that ends[j] <= starts[i]
    # Using bisect_right on the ends array gives us the rightmost position where ends[pos] <= starts[i]
    # But we need j < i. Since ends is sorted, bisect_right(ends, starts[i]) gives us the count of elements <= starts[i].
    # Let pos = bisect_right(ends, starts[i]) - 1, which is the largest index with ends[pos] <= starts[i].
    # But we also need pos < i. Since ends[i] > starts[i] (because start < end for each job), and ends is sorted,
    # ends[i] > starts[i], so pos < i is guaranteed if pos exists.
    
    # Actually, let's just use bisect_right(ends, starts[i]) which gives the number of elements <= starts[i].
    # Let count = bisect_right(ends, starts[i]). Then the compatible job index in 1-indexed dp is count (since dp is 1-indexed, dp[count] represents the best up to job count-1 in 0-indexed).
    
    # Let me redefine:
    # dp[i] for i in 0..n, where dp[0] = 0
    # For job i (1-indexed, corresponding to indexed_jobs[i-1]):
    #   p = bisect_right(ends, starts[i-1])  # number of jobs with end <= starts[i-1]
    #   dp[i] = max(dp[i-1], weights[i-1] + dp[p])
    
    # To reconstruct, we need to track choices.
    
    dp = [0.0] * (n + 1)
    # choice[i] = True if we chose job i (1-indexed), False otherwise
    choice = [False] * (n + 1)
    
    for i in range(1, n + 1):
        # Job i-1 in 0-indexed
        s = starts[i - 1]
        # Find p: number of jobs with end <= s
        p = bisect.bisect_right(ends, s)
        # p is in range [0, i-1] since ends[i-1] > s (start < end)
        take = weights[i - 1] + dp[p]
        skip = dp[i - 1]
        if take >= skip:
            dp[i] = take
            choice[i] = True
        else:
            dp[i] = skip
            choice[i] = False
    
    # Reconstruct the chosen jobs
    chosen = []
    i = n
    while i > 0:
        if choice[i]:
            chosen.append(i - 1)  # 0-indexed in sorted array
            # Move to p(i)
            s = starts[i - 1]
            p = bisect.bisect_right(ends, s)
            i = p
        else:
            i -= 1
    
    # chosen contains 0-indexed positions in the sorted array
    # Map back to original indices
    original_indices = [orig_indices[idx] for idx in chosen]
    
    # Sort by start time, then by original index
    # We need to sort the chosen jobs by their start time, breaking ties by original index
    # Get the start times for the chosen jobs
    chosen_with_info = []
    for idx in chosen:
        orig_idx = orig_indices[idx]
        start_time = jobs[orig_idx][0]
        chosen_with_info.append((start_time, orig_idx))
    
    chosen_with_info.sort(key=lambda x: (x[0], x[1]))
    
    final_indices = [x[1] for x in chosen_with_info]
    
    return (dp[n], final_indices)
