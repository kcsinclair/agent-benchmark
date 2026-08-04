def best_schedule(jobs):
    """
    Find the maximum weight subset of non-overlapping jobs.
    
    Args:
        jobs: List of (start, end, weight) tuples
        
    Returns:
        Tuple of (total_weight, chosen_indices) where:
        - total_weight is the maximum achievable sum of weights
        - chosen_indices are the indices of jobs in the optimal subset
    """
    if not jobs:
        return (0.0, [])
    
    # Create list of (start, end, weight, index) for easier handling
    indexed_jobs = [(start, end, weight, i) for i, (start, end, weight) in enumerate(jobs)]
    indexed_jobs.sort()  # Sort by start time
    
    # Extract sorted arrays for easier access
    starts = [job[0] for job in indexed_jobs]
    ends = [job[1] for job in indexed_jobs]
    weights = [job[2] for job in indexed_jobs]
    indices = [job[3] for job in indexed_jobs]
    
    n = len(jobs)
    
    # Precompute the latest non-overlapping job for each job
    # For job i, find the latest job j such that job j ends <= job i starts
    latest_non_overlap = [-1] * n  # -1 means no such job exists
    
    # Binary search for the latest non-overlapping job
    for i in range(1, n):
        # Find the rightmost job that ends <= current job's start
        left, right = 0, i - 1
        pos = -1
        
        while left <= right:
            mid = (left + right) // 2
            if ends[mid] <= starts[i]:
                pos = mid
                left = mid + 1
            else:
                right = mid - 1
        
        latest_non_overlap[i] = pos
    
    # Dynamic programming
    # dp[i] represents the maximum weight achievable using jobs 0..i
    dp = [0.0] * n
    dp[0] = weights[0]
    
    for i in range(1, n):
        # Option 1: Don't take current job
        option1 = dp[i-1]
        
        # Option 2: Take current job
        # We can take this job if we don't overlap with previous jobs
        # If we take job i, we can add its weight to the best solution
        # that doesn't overlap with job i
        if latest_non_overlap[i] == -1:
            # No previous non-overlapping job
            option2 = weights[i]
        else:
            # Add current job's weight to the best solution up to latest_non_overlap[i]
            option2 = weights[i] + dp[latest_non_overlap[i]]
        
        dp[i] = max(option1, option2)
    
    # Reconstruct the solution
    # Backtrack to find which jobs were selected
    selected_indices = []
    i = n - 1
    
    # Use iterative approach to avoid recursion limit
    while i >= 0:
        if i == 0:
            if dp[i] > 0:
                selected_indices.append(indices[i])
            break
        
        # If we took job i, then dp[i] = weights[i] + dp[latest_non_overlap[i]]
        # Otherwise, dp[i] = dp[i-1]
        if latest_non_overlap[i] == -1:
            # No previous non-overlapping job
            if dp[i] == weights[i]:
                selected_indices.append(indices[i])
                i -= 1
            else:
                i -= 1
        else:
            # Check if we took this job
            if dp[i] == weights[i] + dp[latest_non_overlap[i]]:
                selected_indices.append(indices[i])
                i = latest_non_overlap[i]
            else:
                i -= 1
    
    # Sort indices by start time (they're already sorted due to our processing)
    selected_indices.sort()
    
    return (dp[n-1], selected_indices)
