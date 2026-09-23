def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solve the weighted interval scheduling problem.
    
    Args:
        jobs: List of (start, end, weight) tuples
        
    Returns:
        (total_weight, chosen_indices) where chosen_indices are sorted by start time
    """
    if not jobs:
        return (0.0, [])
    
    # Create list of (start, end, weight, original_index)
    indexed_jobs = [(jobs[i][0], jobs[i][1], jobs[i][2], i) for i in range(len(jobs))]
    
    # Sort by end time, then by start time, then by original index for stability
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    n = len(indexed_jobs)
    
    # dp[i] = (max_weight, last_job_index_in_solution)
    # We store the maximum weight and which job was last included to enable reconstruction
    dp = [(0.0, -1)] * (n + 1)  # dp[0] = (0, -1) for base case
    
    for i in range(n):
        start_i, end_i, weight_i, orig_idx_i = indexed_jobs[i]
        
        # Find the latest job that ends <= start_i using binary search
        # We search in the sorted list for the rightmost job with end_time <= start_i
        left, right = 0, i - 1
        latest_compatible = -1
        
        while left <= right:
            mid = (left + right) // 2
            if indexed_jobs[mid][1] <= start_i:
                latest_compatible = mid
                left = mid + 1
            else:
                right = mid - 1
        
        # Option 1: Don't take job i
        option_without = dp[i][0]
        
        # Option 2: Take job i
        if latest_compatible == -1:
            option_with = weight_i
        else:
            option_with = dp[latest_compatible + 1][0] + weight_i
        
        # Choose the better option
        if option_with > option_without:
            dp[i + 1] = (option_with, i)
        else:
            dp[i + 1] = (option_without, dp[i][1])
    
    # Reconstruct the solution
    max_weight = dp[n][0]
    chosen_indices_sorted = []
    
    # Backtrack to find which jobs were selected
    current_idx = n
    while current_idx > 0:
        last_job_idx = dp[current_idx][1]
        if last_job_idx == -1:
            break
        
        # Job at last_job_idx was included
        chosen_indices_sorted.append(indexed_jobs[last_job_idx][3])  # original index
        
        # Move to the position before this job
        start_of_last = indexed_jobs[last_job_idx][0]
        
        # Find the rightmost job that ends <= start_of_last
        left, right = 0, last_job_idx - 1
        next_idx = 0
        
        while left <= right:
            mid = (left + right) // 2
            if indexed_jobs[mid][1] <= start_of_last:
                next_idx = mid + 1
                left = mid + 1
            else:
                right = mid - 1
        
        current_idx = next_idx
    
    # Sort chosen indices by the start time of their jobs (and by index as tiebreaker)
    chosen_indices_sorted.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (max_weight, chosen_indices_sorted)
