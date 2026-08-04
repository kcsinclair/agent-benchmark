import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of (start, end, weight) tuples.
        
    Returns:
        A tuple (total_weight, chosen_indices) where chosen_indices are 
        sorted by start time.
    """
    if not jobs:
        return (0.0, [])

    # 1. Store original indices and sort jobs by end time.
    # Sorting by end time is the standard approach for the DP solution.
    # indexed_jobs: (start, end, weight, original_index)
    indexed_jobs = []
    for i, (s, e, w) in enumerate(jobs):
        indexed_jobs.append((s, e, w, i))
    
    # Sort by end time ascending.
    indexed_jobs.sort(key=lambda x: x[1])
    
    n = len(indexed_jobs)
    # dp[i] stores the maximum weight achievable using a subset of the first i jobs.
    dp = [0.0] * (n + 1)
    # parent[i] stores whether the i-th job (1-indexed) was included in the optimal solution for dp[i].
    # If included, we store the index of the previous compatible job. Otherwise, we store -1.
    parent = [-1] * (n + 1)
    
    # Extract end times for binary search.
    end_times = [job[1] for job in indexed_jobs]
    
    for i in range(1, n + 1):
        start, end, weight, idx = indexed_jobs[i-1]
        
        # Find the rightmost job that ends before or at the start time of the current job.
        # bisect_right finds the insertion point to maintain order.
        # Since we want end_times[j] <= start, bisect_right on end_times gives us 
        # the index of the first element > start. Subtracting 1 gives the last element <= start.
        prev_idx = bisect.bisect_right(end_times, start)
        
        # Option 1: Include the current job.
        include_weight = weight + dp[prev_idx]
        
        # Option 2: Exclude the current job.
        exclude_weight = dp[i-1]
        
        if include_weight > exclude_weight:
            dp[i] = include_weight
            parent[i] = prev_idx # Mark that we took job i-1 and jumped back to prev_idx
        else:
            dp[i] = exclude_weight
            parent[i] = -2 # Mark that we skipped job i-1

    # Backtrack to find the indices of the chosen jobs.
    chosen_indices = []
    curr = n
    while curr > 0:
        if parent[curr] == -2:
            curr -= 1
        else:
            # Job at index curr-1 was included.
            chosen_indices.append(indexed_jobs[curr-1][3])
            curr = parent[curr]
            
    # The problem requires chosen_indices to be sorted by the job's start time.
    # We retrieve the start times using the original indices.
    # Sort by (start_time, original_index).
    final_indices = sorted(chosen_indices, key=lambda idx: (jobs[idx][0], idx))
    
    return (float(dp[n]), final_indices)
