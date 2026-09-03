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

    # We need to keep track of original indices to return them at the end.
    # indexed_jobs: list of (start, end, weight, original_index)
    indexed_jobs = []
    for i, (s, e, w) in enumerate(jobs):
        indexed_jobs.append((s, e, w, i))

    # Sort jobs by end time to facilitate dynamic programming.
    # O(n log n)
    indexed_jobs.sort(key=lambda x: x[1])

    n = len(indexed_jobs)
    
    # dp[i] will store the maximum weight achievable using a subset of 
    # the first i jobs (from the sorted list).
    # dp_indices[i] will store the index of the job that was added to 
    # achieve dp[i], or -1 if no job was added (or if dp[i] == dp[i-1]).
    # To reconstruct the path, we store the index of the 'previous' job 
    # in the DP sequence.
    
    dp = [0.0] * (n + 1)
    # parent[i] stores the index in the 'dp' array of the previous job 
    # used to reach the optimal weight at dp[i].
    parent = [0] * (n + 1)
    # job_used[i] stores the index in 'indexed_jobs' that was used to reach dp[i].
    job_used = [-1] * (n + 1)

    # Extract end times for binary search
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start, end, weight, original_idx = indexed_jobs[i-1]
        
        # Find the latest job that ends before or at the current job's start time.
        # bisect_right finds the first index where end_time > start.
        # Subtracting 1 gives the index of the last job where end_time <= start.
        idx = bisect.bisect_right(end_times, start)
        
        # Option 1: Include the current job
        weight_with_current = weight + dp[idx]
        
        # Option 2: Exclude the current job
        weight_without_current = dp[i-1]
        
        if weight_with_current > weight_without_current:
            dp[i] = weight_with_current
            parent[i] = idx
            job_used[i] = i - 1
        else:
            dp[i] = weight_without_current
            parent[i] = i - 1
            job_used[i] = -1

    # Reconstruct the solution by backtracking through the DP table.
    chosen_indices = []
    curr = n
    while curr > 0:
        if job_used[curr] != -1:
            # This job was part of the optimal solution for dp[curr]
            idx_in_sorted = job_used[curr]
            chosen_indices.append(indexed_jobs[idx_in_sorted][3])
            curr = parent[curr]
        else:
            # This job was not used; move to the previous state
            curr = parent[curr]

    # The problem requires indices sorted by start time.
    # Since we backtracked, they are currently in reverse order of end times.
    # We sort them based on the start time of the original jobs.
    # To do this efficiently, we use the original jobs list to look up start times.
    
    # Note: The problem says "sorted by the job's start time (break ties by index ascending)".
    # We'll create a list of (start_time, original_index) for the chosen jobs.
    
    final_selection = []
    for idx in chosen_indices:
        final_selection.append((jobs[idx][0], idx))
    
    # Sort by start time, then by index
    final_selection.sort()
    
    result_indices = [item[1] for item in final_selection]

    return (float(dp[n]), result_indices)
