def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Find the maximum weight subset of non-overlapping jobs.
    
    Args:
        jobs: List of (start, end, weight) tuples
        
    Returns:
        Tuple of (max_weight, chosen_indices) where chosen_indices are 
        the indices of jobs in the optimal solution, sorted by start time
    """
    if not jobs:
        return (0.0, [])
    
    # Create list of (start, end, weight, index) for easier processing
    indexed_jobs = [(start, end, weight, i) for i, (start, end, weight) in enumerate(jobs)]
    indexed_jobs.sort()  # Sort by start time
    
    # Extract sorted components for easier access
    starts = [job[0] for job in indexed_jobs]
    ends = [job[1] for job in indexed_jobs]
    weights = [job[2] for job in indexed_jobs]
    indices = [job[3] for job in indexed_jobs]
    
    n = len(jobs)
    
    # For each job, find the latest non-overlapping job (using binary search)
    # We want the rightmost job that ends <= current job's start
    def find_latest_non_overlapping(job_index):
        # Binary search for the rightmost job that ends <= current job's start
        target = starts[job_index]
        left, right = 0, job_index - 1
        result = -1
        
        while left <= right:
            mid = (left + right) // 2
            if ends[mid] <= target:
                result = mid
                left = mid + 1
            else:
                right = mid - 1
                
        return result
    
    # DP array: dp[i] represents the maximum weight achievable using jobs 0..i
    dp = [0.0] * n
    
    # Base case
    dp[0] = weights[0]
    
    # Fill DP table
    for i in range(1, n):
        # Option 1: Don't take current job
        option1 = dp[i-1]
        
        # Option 2: Take current job + best solution up to last non-overlapping job
        latest_non_overlapping = find_latest_non_overlapping(i)
        if latest_non_overlapping == -1:
            option2 = weights[i]
        else:
            option2 = weights[i] + dp[latest_non_overlapping]
        
        dp[i] = max(option1, option2)
    
    # Reconstruct the solution
    # We need to trace back which jobs were selected
    selected_indices = []
    i = n - 1
    
    # Use iterative approach to avoid recursion limit issues
    while i >= 0:
        if i == 0:
            if dp[i] > 0:
                selected_indices.append(indices[i])
            break
            
        # If we took this job, then dp[i] = weights[i] + dp[latest_non_overlapping]
        # Otherwise, dp[i] = dp[i-1]
        latest_non_overlapping = find_latest_non_overlapping(i)
        
        if latest_non_overlapping == -1:
            if weights[i] >= dp[i-1]:
                selected_indices.append(indices[i])
                i -= 1
            else:
                i -= 1
        else:
            if weights[i] + dp[latest_non_overlapping] >= dp[i-1]:
                selected_indices.append(indices[i])
                i = latest_non_overlapping
            else:
                i -= 1
    
    # Sort selected indices by start time (which is the same as original order)
    selected_indices.sort()
    
    return (dp[n-1], selected_indices)
