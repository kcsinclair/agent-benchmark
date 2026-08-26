def best_schedule(jobs):
    """
    Find the maximum weight subset of non-overlapping jobs.
    
    Args:
        jobs: List of (start, end, weight) tuples
        
    Returns:
        Tuple of (total_weight, chosen_indices) where total_weight is the 
        maximum achievable sum of weights and chosen_indices are the indices 
        of jobs in the optimal subset, sorted by start time
    """
    if not jobs:
        return (0.0, [])
    
    # Create list of (start, end, weight, index) for easier handling
    indexed_jobs = [(start, end, weight, i) for i, (start, end, weight) in enumerate(jobs)]
    
    # Sort by end time
    indexed_jobs.sort(key=lambda x: x[1])
    
    n = len(indexed_jobs)
    
    # dp[i] represents the maximum weight achievable using jobs 0 to i-1
    dp = [0.0] * (n + 1)
    
    # For each job, we need to find the latest job that doesn't overlap
    # We'll use binary search for efficiency
    def find_latest_non_overlapping(start_time):
        """Find the latest job whose end time <= start_time"""
        # Binary search for the rightmost job with end_time <= start_time
        left, right = 0, n - 1
        result = -1
        
        while left <= right:
            mid = (left + right) // 2
            if indexed_jobs[mid][1] <= start_time:
                result = mid
                left = mid + 1
            else:
                right = mid - 1
                
        return result
    
    # Fill the dp array
    for i in range(n):
        # Option 1: Don't take current job
        dp[i + 1] = dp[i]
        
        # Option 2: Take current job
        current_weight = indexed_jobs[i][2]
        latest_non_overlapping = find_latest_non_overlapping(indexed_jobs[i][0])
        
        if latest_non_overlapping == -1:
            # No previous non-overlapping job
            dp[i + 1] = max(dp[i + 1], current_weight)
        else:
            # Take current job + best from non-overlapping jobs
            dp[i + 1] = max(dp[i + 1], current_weight + dp[latest_non_overlapping + 1])
    
    # Now we need to reconstruct the solution
    # Backtrack to find which jobs were selected
    selected_indices = []
    i = n - 1
    current_weight = dp[n]
    
    # We'll go backwards through the dp array to find selected jobs
    while i >= 0 and current_weight > 0:
        # If dp[i+1] == dp[i], we didn't take job i
        if dp[i + 1] == dp[i]:
            i -= 1
        else:
            # We took job i
            selected_indices.append(indexed_jobs[i][3])
            current_weight -= indexed_jobs[i][2]
            # Find the latest non-overlapping job
            latest_non_overlapping = find_latest_non_overlapping(indexed_jobs[i][0])
            if latest_non_overlapping == -1:
                break
            else:
                i = latest_non_overlapping
    
    # Sort selected indices by start time (and by index for ties)
    selected_indices.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (dp[n], selected_indices)
