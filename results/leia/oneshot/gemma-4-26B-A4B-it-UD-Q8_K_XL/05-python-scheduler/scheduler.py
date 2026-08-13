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
    # achieve dp[i], or -1 if no job was added at that step.
    # prev_dp_idx[i] will store the index in the dp array of the 
    # previous compatible job.
    
    dp = [0.0] * (n + 1)
    # To reconstruct the path, we store which job was chosen at step i.
    # chosen_job_idx[i] = index in indexed_jobs if job i was part of the optimal solution for dp[i+1]
    # However, a simpler way for reconstruction:
    # parent[i] = the index of the last job in the optimal subset ending at or before job i's end time.
    
    # end_times stores the end times of the sorted jobs for binary search.
    end_times = [job[1] for job in indexed_jobs]
    
    # decision[i] = True if the i-th job (in sorted order) was included in the optimal solution for dp[i+1]
    decision = [False] * n
    # prev_compatible[i] = the index of the latest job that ends before job i starts.
    prev_compatible = [-1] * n

    for i in range(n):
        start, end, weight, _ = indexed_jobs[i]
        
        # Find the latest job that ends at or before the current job's start time.
        # bisect_right finds the first index where end_time > start.
        # Subtracting 1 gives the index of the job where end_time <= start.
        idx = bisect.bisect_right(end_times, start) - 1
        
        # If idx is >= i, it means we found a job that ends after current job starts 
        # (due to sorting/duplicates), but bisect_right on end_times ensures 
        # we find the rightmost compatible job. We must ensure idx < i.
        if idx >= i:
            idx = i - 1
            
        prev_compatible[i] = idx
        
        # Weight if we include job i
        weight_if_included = weight + (dp[idx + 1] if idx != -1 else 0.0)
        
        # Weight if we exclude job i
        weight_if_excluded = dp[i]
        
        if weight_if_included > weight_if_excluded:
            dp[i + 1] = weight_if_included
            decision[i] = True
        else:
            dp[i + 1] = weight_if_excluded
            decision[i] = False

    # Reconstruct the solution
    chosen_indices = []
    curr = n - 1
    while curr >= 0:
        if decision[curr]:
            # Job curr was included
            chosen_indices.append(indexed_jobs[curr][3])
            # Move to the last compatible job
            curr = prev_compatible[curr]
        else:
            # Job curr was not included, move to the previous job in sorted list
            curr -= 1

    # The problem asks for indices sorted by start time.
    # Since we reconstructed backwards, we reverse and then sort by start time.
    # However, the requirement is: "sorted by the job's start time (break ties by index ascending)".
    
    # Let's collect the actual job objects to sort them correctly.
    final_jobs = []
    for idx in chosen_indices:
        final_jobs.append(jobs[idx])
    
    # We need to return the original indices. Let's re-map.
    # The indices in chosen_indices are already the original indices.
    # We need to sort these indices based on the start time of the corresponding job.
    
    # Create a list of (start_time, original_index) for the chosen jobs
    sort_keys = []
    for idx in chosen_indices:
        sort_keys.append((jobs[idx][0], idx))
    
    # Sort by start time, then by index
    sort_keys.sort()
    
    result_indices = [item[1] for item in sort_keys]

    return (float(dp[n]), result_indices)
