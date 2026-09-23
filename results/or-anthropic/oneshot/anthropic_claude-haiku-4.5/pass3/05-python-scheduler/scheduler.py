"""
Weighted Interval Scheduling at Scale

Solves the weighted interval scheduling problem in O(n log n) time using
dynamic programming with binary search.

Key insight: Sort jobs by end time, then use DP where dp[i] = maximum weight
achievable using jobs 0..i. For each job i, either:
  1. Skip it: dp[i] = dp[i-1]
  2. Take it: dp[i] = weight[i] + dp[p(i)], where p(i) is the latest job
     that doesn't overlap with job i

Use binary search to find p(i) efficiently.
"""

import bisect
from typing import List, Tuple


def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """
    Find the maximum weight subset of non-overlapping jobs.
    
    Args:
        jobs: List of (start, end, weight) tuples where start < end and weight > 0
        
    Returns:
        (total_weight, chosen_indices) where chosen_indices are sorted by job start time
    """
    if not jobs:
        return (0.0, [])
    
    n = len(jobs)
    
    # Create list of (end_time, start_time, weight, original_index)
    # Sort by end time, with ties broken by original index for stability
    indexed_jobs = [
        (jobs[i][1], jobs[i][0], jobs[i][2], i)
        for i in range(n)
    ]
    indexed_jobs.sort()
    
    # Extract sorted data
    ends = [job[0] for job in indexed_jobs]
    starts = [job[1] for job in indexed_jobs]
    weights = [job[2] for job in indexed_jobs]
    original_indices = [job[3] for job in indexed_jobs]
    
    # dp[i] = (max_weight, last_job_index_in_solution)
    # We track the last job index to reconstruct the solution
    dp = [(0.0, -1)] * (n + 1)  # dp[0] = (0, -1) as base case
    
    for i in range(n):
        # Find the latest job that doesn't overlap with job i
        # Job j doesn't overlap with job i if ends[j] <= starts[i]
        # We want the largest j such that ends[j] <= starts[i]
        
        # Binary search for the rightmost position where end <= starts[i]
        pos = bisect.bisect_right(ends, starts[i], 0, i) - 1
        
        # pos is now the index of the latest non-overlapping job (or -1 if none)
        prev_weight = dp[pos + 1][0] if pos >= 0 else 0.0
        
        # Option 1: Take job i
        take_weight = prev_weight + weights[i]
        take_last = i
        
        # Option 2: Skip job i
        skip_weight = dp[i][0]
        skip_last = dp[i][1]
        
        if take_weight > skip_weight:
            dp[i + 1] = (take_weight, take_last)
        else:
            dp[i + 1] = (skip_weight, skip_last)
    
    # Reconstruct solution by backtracking
    total_weight, _ = dp[n]
    
    # Backtrack to find which jobs were selected
    chosen_sorted_indices = []
    current = n
    
    while current > 0:
        weight, last_job = dp[current]
        prev_weight = dp[current - 1][0]
        
        # Check if job at current-1 was taken
        if last_job == current - 1:
            # Job current-1 was taken
            chosen_sorted_indices.append(current - 1)
            # Find the latest non-overlapping job before this one
            pos = bisect.bisect_right(ends, starts[current - 1], 0, current - 1) - 1
            current = pos + 1
        else:
            current -= 1
    
    # Convert sorted indices back to original indices
    chosen_original_indices = [original_indices[i] for i in chosen_sorted_indices]
    
    # Sort by original job start time (with ties broken by original index)
    chosen_original_indices.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (total_weight, chosen_original_indices)
