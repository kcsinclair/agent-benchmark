def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Find the maximum weight subset of non-overlapping jobs.
    
    Args:
        jobs: List of (start, end, weight) tuples
        
    Returns:
        Tuple of (max_weight, list of job indices in optimal solution)
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
    latest_non_overlap = [-1] * n  # -1 means no previous non-overlapping job
    
    # Binary search to find latest non-overlapping job
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
    # dp[i] = maximum weight achievable using jobs 0..i
    dp = [0.0] * n
    dp[0] = weights[0]
    
    for i in range(1, n):
        # Option 1: Don't take current job
        option1 = dp[i-1]
        
        # Option 2: Take current job
        # Weight of current job + weight of best solution up to latest non-overlapping job
        option2 = weights[i]
        if latest_non_overlap[i] != -1:
            option2 += dp[latest_non_overlap[i]]
        
        dp[i] = max(option1, option2)
    
    # Reconstruct the solution
    # Backtrack to find which jobs were selected
    selected_indices = []
    i = n - 1
    
    # We'll use a stack to collect indices in reverse order, then reverse
    while i >= 0:
        if i == 0:
            if dp[i] > 0:
                selected_indices.append(indices[i])
            break
        
        # If taking job i gives better result than not taking it
        if dp[i] != dp[i-1]:
            selected_indices.append(indices[i])
            # Find the latest non-overlapping job
            prev = latest_non_overlap[i]
            if prev == -1:
                break
            i = prev
        else:
            i -= 1
    
    # Reverse to get indices in increasing order of start time
    selected_indices.reverse()
    
    return (dp[n-1], selected_indices)
