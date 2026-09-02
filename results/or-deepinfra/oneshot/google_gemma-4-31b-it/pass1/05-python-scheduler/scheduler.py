import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of (start, end, weight) tuples.
        
    Returns:
        A tuple (total_weight, chosen_indices) where chosen_indices are the 
        indices of the jobs in the original input list.
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
    # dp[i] will store the maximum weight achievable using a subset of the first i jobs.
    dp = [0.0] * (n + 1)
    # parent[i] stores whether the i-th job (1-indexed) was included in the optimal solution for dp[i].
    # If included, parent[i] = index of the last compatible job. Otherwise, parent[i] = -1.
    parent = [-1] * (n + 1)
    
    # To perform binary search on end times efficiently.
    end_times = [job[1] for job in indexed_jobs]
    
    for i in range(1, n + 1):
        start, end, weight, idx = indexed_jobs[i-1]
        
        # Find the rightmost job that ends before or at the start time of the current job.
        # bisect_right finds the insertion point to maintain order.
        # Since we want end_time <= start, bisect_right on end_times gives the index 
        # of the first element > start. The element before that is <= start.
        prev_idx = bisect.bisect_right(end_times, start)
        
        # We must ensure we don't pick the current job itself if it's the one found.
        # Since end_times is sorted and we are at index i-1, and start < end,
        # prev_idx will naturally be <= i-1.
        if prev_idx > i - 1:
            prev_idx = i - 1
            
        # Option 1: Include job i-1. Total weight = weight + dp[prev_idx]
        # Option 2: Exclude job i-1. Total weight = dp[i-1]
        include_weight = weight + dp[prev_idx]
        exclude_weight = dp[i-1]
        
        if include_weight > exclude_weight:
            dp[i] = include_weight
            parent[i] = prev_idx # Mark that we included job i-1 and came from prev_idx
        else:
            dp[i] = exclude_weight
            parent[i] = -2 # Mark that we excluded job i-1

    # Backtrack to find the indices of the chosen jobs.
    chosen_indices = []
    curr = n
    while curr > 0:
        if parent[curr] == -2:
            # Job curr-1 was not included.
            curr -= 1
        else:
            # Job curr-1 was included.
            job_idx = indexed_jobs[curr-1][3]
            chosen_indices.append(job_idx)
            curr = parent[curr]
            
    # The problem asks for indices sorted by the job's start time.
    # We retrieve the start times from the original jobs list.
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (float(dp[n]), chosen_indices)
