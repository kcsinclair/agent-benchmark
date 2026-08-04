import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of tuples (start, end, weight).
        
    Returns:
        A tuple (total_weight, chosen_indices) where chosen_indices is a list
        of indices into the original jobs list, sorted by start time.
    """
    if not jobs:
        return 0.0, []

    # We need to keep track of original indices to return them at the end.
    # Format: (end, start, weight, original_index)
    indexed_jobs = []
    for i, (s, e, w) in enumerate(jobs):
        indexed_jobs.append((e, s, w, i))

    # Sort jobs by end time to facilitate dynamic programming.
    # O(n log n)
    indexed_jobs.sort()

    n = len(indexed_jobs)
    # dp[i] will store the maximum weight achievable using a subset of 
    # the first i jobs (from the sorted list).
    dp = [0.0] * (n + 1)
    
    # To reconstruct the solution, we store whether the i-th job was included.
    # included[i] = True if job i-1 (in sorted list) was part of the optimal solution for dp[i].
    included = [False] * (n + 1)
    
    # We also need to know the index of the last compatible job for each job.
    # p[i] is the index in the sorted list of the last job that ends before 
    # the i-th job starts.
    p = [0] * n
    
    # Extract end times for binary search
    end_times = [job[0] for job in indexed_jobs]

    for i in range(n):
        e_i, s_i, w_i, idx_i = indexed_jobs[i]
        
        # Find the rightmost job whose end time <= current job's start time.
        # bisect_right returns the insertion point which is the index of the 
        # first element > s_i. Subtracting 1 gives the index of the last element <= s_i.
        idx = bisect.bisect_right(end_times, s_i) - 1
        
        # If idx is -1, no job ends before this one starts.
        # Otherwise, the compatible job is at index idx in the sorted list.
        # In our 1-based DP, this corresponds to dp[idx + 1].
        p[i] = idx
        
        # Option 1: Include current job
        weight_if_included = w_i + (dp[idx + 1] if idx >= 0 else 0.0)
        
        # Option 2: Exclude current job
        weight_if_excluded = dp[i] # dp[i] is the max weight using first i jobs
        
        if weight_if_included > weight_if_excluded:
            dp[i + 1] = weight_if_included
            included[i + 1] = True
        else:
            dp[i + 1] = weight_if_excluded
            included[i + 1] = False

    # Reconstruct the solution by backtracking through the 'included' array.
    total_weight = dp[n]
    chosen_indices = []
    curr = n
    while curr > 0:
        if included[curr]:
            # The job at index curr-1 in the sorted list was included.
            job_idx = indexed_jobs[curr - 1][3]
            chosen_indices.append(job_idx)
            # Move to the last compatible job.
            curr = p[curr - 1] + 1
        else:
            # The job was not included, move to the previous job in sorted list.
            curr -= 1

    # The problem requires indices to be sorted by start time.
    # Since we backtracked, they are currently in reverse order of end times.
    # We sort them based on the start time of the original jobs.
    # Note: The problem says "sorted by the job's start time (break ties by index ascending)".
    # We'll use the original jobs list to get start times for sorting.
    chosen_indices.sort(key=lambda i: (jobs[i][0], i))

    return float(total_weight), chosen_indices
