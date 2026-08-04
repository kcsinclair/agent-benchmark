"""
Weighted Interval Scheduling at Scale.

Solves the weighted interval scheduling problem in O(n log n) time.
"""

from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Choose a subset of non-overlapping jobs maximizing total weight.
    
    Args:
        jobs: List of (start, end, weight) tuples.
        
    Returns:
        (total_weight, chosen_indices) where chosen_indices are indices into
        the original input list, sorted by start time (ties broken by index).
    """
    if not jobs:
        return (0.0, [])
    
    n = len(jobs)
    
    # Create indexed jobs: (start, end, weight, original_index)
    indexed_jobs = [(jobs[i][0], jobs[i][1], jobs[i][2], i) for i in range(n)]
    
    # Sort by end time (primary), then by start time (secondary) for stability
    indexed_jobs.sort(key=lambda x: (x[1], x[0]))
    
    # Extract sorted end times for binary search
    end_times = [job[1] for job in indexed_jobs]
    
    # dp[i] = maximum weight achievable considering jobs 0..i (in sorted order)
    # We use iterative DP to avoid recursion limit issues.
    dp = [0.0] * n
    
    # For backtracking: choice[i] = True if we include job i in the optimal solution
    # for the subproblem considering jobs 0..i
    choice = [False] * n
    
    for i in range(n):
        start_i, end_i, weight_i, orig_idx_i = indexed_jobs[i]
        
        # Option 1: Don't include job i
        exclude_weight = dp[i - 1] if i > 0 else 0.0
        
        # Option 2: Include job i
        # Find the latest job j < i such that end_j <= start_i (non-overlapping)
        # We need the largest index j where end_times[j] <= start_i
        # bisect_right gives us the insertion point, so we subtract 1
        j = bisect_right(end_times, start_i, 0, i) - 1
        
        include_weight = weight_i
        if j >= 0:
            include_weight += dp[j]
        
        if include_weight >= exclude_weight:
            dp[i] = include_weight
            choice[i] = True
        else:
            dp[i] = exclude_weight
            choice[i] = False
    
    # Backtrack to find chosen jobs
    chosen_sorted_indices = []  # indices into indexed_jobs (sorted order)
    i = n - 1
    while i >= 0:
        if choice[i]:
            chosen_sorted_indices.append(i)
            # Jump to the last compatible job
            start_i = indexed_jobs[i][0]
            j = bisect_right(end_times, start_i, 0, i) - 1
            i = j
        else:
            i -= 1
    
    # Convert from sorted-order indices to original indices
    original_indices = [indexed_jobs[idx][3] for idx in chosen_sorted_indices]
    
    # Sort by start time (break ties by original index ascending)
    # We need to look up the start times from the original jobs list
    original_indices.sort(key=lambda idx: (jobs[idx][0], idx))
    
    total_weight = dp[n - 1]
    
    return (total_weight, original_indices)
