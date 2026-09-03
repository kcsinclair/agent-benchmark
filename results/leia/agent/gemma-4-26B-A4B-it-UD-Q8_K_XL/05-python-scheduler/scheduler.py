from bisect import bisect_right

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
        return 0.0, []

    n = len(jobs)
    # Store jobs with their original index to reconstruct the solution
    # indexed_jobs[i] = (start, end, weight, original_index)
    indexed_jobs = []
    for i in range(n):
        indexed_jobs.append((jobs[i][0], jobs[i][1], jobs[i][2], i))

    # Sort jobs by end time to facilitate dynamic programming
    indexed_jobs.sort(key=lambda x: x[1])

    # dp[i] will store the maximum weight using a subset of the first i jobs (1-indexed)
    dp = [0.0] * (n + 1)
    # included[i] stores whether job i-1 was included in the optimal subset for dp[i]
    included = [False] * (n + 1)
    # prev_compatible_idx[i] stores the index j such that job j-1 is the last compatible job before job i-1
    prev_compatible_idx = [0] * (n + 1)

    # Extract end times for binary search
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start_i, end_i, weight_i, _ = indexed_jobs[i-1]
        
        # Find the latest job that ends before or at the start time of the current job
        # bisect_right returns the index after the last element <= start_i
        # We need the largest j such that end_times[j-1] <= start_i.
        # bisect_right(end_times, start_i) gives the index of the first element > start_i.
        # So j = bisect_right(end_times, start_i) is exactly the number of elements <= start_i.
        # Since dp is 1-indexed, dp[j] is the max weight using the first j jobs.
        j = bisect_right(end_times, start_i)
        
        # If we include job i-1:
        weight_if_included = weight_i + dp[j]
        
        # If we exclude job i-1:
        weight_if_excluded = dp[i-1]
        
        # Use a small epsilon for float comparison to handle precision issues if necessary,
        # but standard comparison is usually fine for this problem type.
        if weight_if_included > weight_if_excluded:
            dp[i] = weight_if_included
            included[i] = True
            prev_compatible_idx[i] = j
        else:
            dp[i] = weight_if_excluded
            included[i] = False

    # Reconstruct the solution
    chosen_indices = []
    curr = n
    while curr > 0:
        if included[curr]:
            # Job indexed_jobs[curr-1] was included
            chosen_indices.append(indexed_jobs[curr-1][3])
            curr = prev_compatible_idx[curr]
        else:
            # Job indexed_jobs[curr-1] was not included
            curr -= 1

    # The problem asks for indices sorted by start time.
    # Tie-break by index ascending.
    # We need to sort the chosen indices based on the start time of the corresponding job.
    
    # Create a list of (start_time, original_index) for the chosen jobs
    final_jobs_info = []
    for idx in chosen_indices:
        final_jobs_info.append((jobs[idx][0], idx))
    
    # Sort by start time, then by original index
    final_jobs_info.sort()
    
    result_indices = [item[1] for item in final_jobs_info]
    
    return float(dp[n]), result_indices
