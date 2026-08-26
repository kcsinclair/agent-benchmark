"""Weighted Interval Scheduling at Scale - O(n log n) solution."""

import bisect


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Choose a non-overlapping subset of jobs maximizing total weight.
    
    Args:
        jobs: list of (start, end, weight) tuples
        
    Returns:
        (total_weight, chosen_indices) where chosen_indices are sorted by
        start time (ties broken by original index ascending)
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])
    
    # Create indexed jobs: (start, end, weight, original_index)
    indexed_jobs = [(jobs[i][0], jobs[i][1], jobs[i][2], i) for i in range(n)]
    
    # Sort by end time, then by start time for stability
    indexed_jobs.sort(key=lambda x: (x[1], x[0]))
    
    # Extract sorted data for easier access
    starts = [j[0] for j in indexed_jobs]
    ends = [j[1] for j in indexed_jobs]
    weights = [j[2] for j in indexed_jobs]
    orig_indices = [j[3] for j in indexed_jobs]
    
    # For each job i, find the largest index j < i such that ends[j] <= starts[i]
    # This is the latest job that doesn't overlap with job i
    # We use binary search on the ends array
    
    # dp[i] = maximum weight achievable using a subset of jobs 0..i (in sorted order)
    # p[i] = the index of the latest non-overlapping predecessor of job i
    
    # Precompute predecessors using binary search
    predecessors = [0] * n
    for i in range(n):
        # Find rightmost job j with ends[j] <= starts[i]
        # bisect_right gives us the insertion point, so we want one less
        pos = bisect.bisect_right(ends, starts[i], 0, i)
        # pos is the count of jobs with end <= starts[i], so the index is pos-1
        predecessors[i] = pos - 1  # -1 means no predecessor
    
    # Iterative DP
    # dp[i] = max weight considering jobs 0..i
    # dp[i] = max(dp[i-1], weights[i] + dp[predecessors[i]])
    # We also track whether we included job i
    
    dp = [0.0] * n
    # include[i] = True if job i is included in the optimal solution for dp[i]
    include = [False] * n
    
    # Base case
    dp[0] = weights[0]
    include[0] = True
    
    for i in range(1, n):
        # Option 1: Don't include job i
        opt1 = dp[i - 1]
        
        # Option 2: Include job i
        pred = predecessors[i]
        if pred >= 0:
            opt2 = weights[i] + dp[pred]
        else:
            opt2 = weights[i]
        
        if opt2 >= opt1:
            dp[i] = opt2
            include[i] = True
        else:
            dp[i] = opt1
            include[i] = False
    
    # Reconstruct the solution
    chosen = []
    i = n - 1
    while i >= 0:
        if include[i]:
            chosen.append(orig_indices[i])
            pred = predecessors[i]
            if pred >= 0:
                i = pred
            else:
                break
        else:
            i -= 1
    
    # Sort chosen indices by start time, then by original index
    # We need to look up the start times from the original jobs
    chosen_with_starts = [(jobs[idx][0], idx) for idx in chosen]
    chosen_with_starts.sort(key=lambda x: (x[0], x[1]))
    chosen_indices = [idx for _, idx in chosen_with_starts]
    
    return (dp[n - 1], chosen_indices)
