"""
Weighted Interval Scheduling at Scale.

Provides best_schedule(jobs) which returns the maximum weight and the indices
of an optimal non-overlapping subset of jobs.
"""

from __future__ import annotations
import bisect
from typing import List, Tuple


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solve the weighted interval scheduling problem.

    Args:
        jobs: A list of (start, end, weight) tuples.

    Returns:
        A tuple (total_weight, chosen_indices) where total_weight is the
        maximum achievable sum of weights and chosen_indices are the indices
        into the input list of one optimal subset, sorted by start time.
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Create a list of (start, end, weight, original_index)
    # We'll sort by end time for the DP.
    indexed_jobs = []
    for i, (s, e, w) in enumerate(jobs):
        indexed_jobs.append((s, e, w, i))

    # Sort by end time. If end times are equal, sort by start time.
    # This ensures a consistent ordering for the DP.
    indexed_jobs.sort(key=lambda x: (x[1], x[0]))

    # dp[i] will store the max weight considering jobs 0..i-1 in the sorted list.
    # dp[0] = 0 (no jobs considered)
    # dp[i] corresponds to considering the first i jobs in the sorted list.
    
    # We need to find for each job j (in sorted order), the latest job k that
    # finishes before or at the start of job j.
    # Since jobs are sorted by end time, we can use binary search on the end times.
    
    # Extract end times for binary search
    end_times = [job[1] for job in indexed_jobs]
    
    # dp array: dp[i] is the max weight using a subset of the first i jobs (sorted by end time)
    # dp[0] = 0
    # For job i (0-indexed in sorted list), which is the (i+1)-th job:
    #   Option 1: Don't include job i. Weight = dp[i]
    #   Option 2: Include job i. Weight = weight_i + dp[p(i)]
    #   where p(i) is the index in the sorted list of the latest job that ends <= start_i.
    #   dp[i+1] = max(dp[i], weight_i + dp[p(i) + 1])
    
    # Let's use a 1-indexed dp array for clarity.
    # dp[k] = max weight using subset of first k jobs (jobs[0]...jobs[k-1] in sorted list)
    dp = [0.0] * (n + 1)
    
    # To reconstruct the solution, we need to know which choice was made.
    # choice[i] = True if job i-1 (in sorted list) was included in the optimal solution for dp[i]
    #            False otherwise.
    # Actually, it's easier to store the decision for each step.
    # Let's store 'include' array: include[i] is True if job i (in sorted list) is included
    # in the optimal solution for dp[i+1].
    include = [False] * n
    
    for i in range(n):
        s, e, w, orig_idx = indexed_jobs[i]
        
        # Find the latest job that ends <= s
        # We search in end_times[0...i-1] for the rightmost value <= s
        # bisect_right returns the insertion point to maintain sorted order.
        # bisect_right(end_times, s, lo=0, hi=i) gives the index where s would be inserted
        # in end_times[0:i] to keep it sorted. All elements before this index are <= s.
        # So the index returned is the count of elements <= s.
        # The job at index (idx - 1) is the last one <= s.
        # We want dp[idx] because dp[k] corresponds to first k jobs.
        
        idx = bisect.bisect_right(end_times, s, lo=0, hi=i)
        # idx is the number of jobs in the sorted list that end <= s.
        # These are jobs 0 to idx-1 in the sorted list.
        # So we can add w to dp[idx].
        
        weight_with_job = w + dp[idx]
        weight_without_job = dp[i]
        
        if weight_with_job >= weight_without_job:
            dp[i + 1] = weight_with_job
            include[i] = True
        else:
            dp[i + 1] = weight_without_job
            include[i] = False

    total_weight = dp[n]
    
    # Reconstruct the solution
    # We need to find which jobs were included.
    # We traverse backwards from i = n-1 to 0.
    chosen_sorted_indices = []  # Indices in the sorted list
    
    i = n - 1
    while i >= 0:
        if include[i]:
            chosen_sorted_indices.append(i)
            # Find the index of the last job that ends <= start of job i
            s, e, w, orig_idx = indexed_jobs[i]
            idx = bisect.bisect_right(end_times, s, lo=0, hi=i)
            # The next job to consider is idx - 1 (since jobs 0..idx-1 are compatible)
            i = idx - 1
        else:
            i -= 1
    
    # chosen_sorted_indices contains indices into the sorted list, in reverse order of inclusion
    # (which is reverse order of end time, but we need to sort by start time for output).
    # Actually, the problem asks for indices sorted by start time.
    # Let's get the original indices and sort them by start time.
    
    chosen_original_indices = []
    for idx in chosen_sorted_indices:
        s, e, w, orig_idx = indexed_jobs[idx]
        chosen_original_indices.append((s, orig_idx))
    
    # Sort by start time, then by original index
    chosen_original_indices.sort(key=lambda x: (x[0], x[1]))
    
    final_indices = [idx for _, idx in chosen_original_indices]
    
    return (total_weight, final_indices)
