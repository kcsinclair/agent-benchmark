import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of (start, end, weight) tuples.
        
    Returns:
        A tuple (total_weight, chosen_indices) where chosen_indices is a 
        list of indices into the original input list.
    """
    if not jobs:
        return (0.0, [])

    # We need to keep track of original indices to return them correctly.
    # Format: (end_time, start_time, weight, original_index)
    indexed_jobs = []
    for i, (s, e, w) in enumerate(jobs):
        indexed_jobs.append((e, s, w, i))

    # Sort jobs by end time to enable Dynamic Programming
    # This allows us to use binary search to find the latest non-overlapping job.
    indexed_jobs.sort()

    n = len(indexed_jobs)
    # dp[i] will store the maximum weight achievable using a subset of the 
    # first i jobs (in the sorted list).
    dp = [0.0] * (n + 1)
    
    # To reconstruct the solution, we store which job was chosen at each step.
    # parent[i] = index of the previous job in the optimal sequence, or -1.
    # choice[i] = True if the i-th job (in sorted list) was included in dp[i].
    choice = [False] * (n + 1)
    parent = [-1] * (n + 1)

    # Extract end times for binary search (bisect_right)
    end_times = [job[0] for job in indexed_jobs]

    for i in range(1, n + 1):
        curr_end, curr_start, curr_weight, curr_idx = indexed_jobs[i-1]
        
        # Find the latest job that ends before or at the current job's start time.
        # bisect_right returns the insertion point which is the index of the 
        # first element > curr_start. Subtracting 1 gives the index of the 
        # last element <= curr_start.
        idx = bisect.bisect_right(end_times, curr_start)
        
        # Option 1: Don't include the current job
        weight_exclude = dp[i-1]
        
        # Option 2: Include the current job
        # We look at the dp value of the compatible job found via binary search.
        # Note: idx is the count of jobs we can skip, which maps to dp[idx].
        weight_include = curr_weight + dp[idx]
        
        if weight_include > weight_exclude:
            dp[i] = weight_include
            choice[i] = True
            parent[i] = idx # Points to the index in the sorted list
        else:
            dp[i] = weight_exclude
            choice[i] = False
            parent[i] = i - 1 # Points to the previous dp state

    # Reconstruct the indices of the chosen jobs
    chosen_indices = []
    curr = n
    while curr > 0:
        if choice[curr]:
            # If this job was chosen, add its original index to the list
            original_idx = indexed_jobs[curr-1][3]
            chosen_indices.append(original_idx)
            # Move to the job that was compatible with this one
            curr = parent[curr]
        else:
            # Move to the previous state
            curr = parent[curr]

    # The problem requires indices sorted by the job's start time.
    # Since we reconstructed them backwards, we sort them based on the 
    # start time of the jobs they represent.
    # However, the prompt says: "sorted by the job's start time (break ties by index ascending)".
    # We'll use the original jobs list to look up start times for sorting.
    
    # Re-sort chosen_indices based on the start time of the jobs they refer to.
    # We use a lambda that retrieves the start time from the original input.
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(dp[n]), chosen_indices)
