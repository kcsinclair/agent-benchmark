import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of (start, end, weight) tuples.
        
    Returns:
        A tuple (total_weight, chosen_indices) where chosen_indices are the 
        original indices of the jobs in the optimal subset, sorted by start time.
    """
    if not jobs:
        return (0.0, [])

    # 1. Store original indices and sort jobs by their end times.
    # Sorting by end time is the standard approach for the DP solution.
    indexed_jobs = []
    for i, (s, e, w) in enumerate(jobs):
        indexed_jobs.append((s, e, w, i))
    
    # Sort by end time ascending.
    indexed_jobs.sort(key=lambda x: x[1])
    
    n = len(indexed_jobs)
    # dp[i] will store the maximum weight achievable using a subset of the first i jobs.
    dp = [0.0] * (n + 1)
    # parent[i] stores whether the i-th job (1-indexed) was included in the optimal solution for dp[i].
    # If included, we store the index of the previous compatible job.
    parent = [-1] * (n + 1)
    
    # To efficiently find the last job that doesn't overlap with the current job,
    # we maintain a list of end times of the sorted jobs.
    end_times = [job[1] for job in indexed_jobs]
    
    for i in range(1, n + 1):
        start, end, weight, original_idx = indexed_jobs[i-1]
        
        # Find the rightmost job that ends <= current job's start time.
        # bisect_right returns the insertion point which is (index + 1).
        idx = bisect.bisect_right(end_times, start)
        
        # We only care about jobs that end before or at the start of the current job.
        # Since end_times is sorted, we check the job at index (idx - 1).
        # However, bisect_right gives us the count of elements <= start.
        # If idx is 3, it means jobs at index 0, 1, 2 in indexed_jobs end <= start.
        # The max weight for those is dp[idx].
        
        # Option 1: Include the current job
        weight_with_current = weight + dp[idx]
        
        # Option 2: Exclude the current job
        weight_without_current = dp[i-1]
        
        if weight_with_current > weight_without_current:
            dp[i] = weight_with_current
            parent[i] = idx # Mark that we took job i and the previous state was dp[idx]
        else:
            dp[i] = weight_without_current
            parent[i] = -2 # Mark that we skipped job i

    # Backtrack to find the indices of the chosen jobs.
    chosen_indices = []
    curr = n
    while curr > 0:
        if parent[curr] == -2:
            curr -= 1
        else:
            # Job (curr-1) was included.
            job_idx = indexed_jobs[curr-1][3]
            chosen_indices.append(job_idx)
            curr = parent[curr]
            
    # The problem asks for indices sorted by the job's start time.
    # We can sort the chosen indices based on the original jobs' start times.
    # Since we need to break ties by index ascending, we use (start, original_index).
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (float(dp[n]), chosen_indices)
