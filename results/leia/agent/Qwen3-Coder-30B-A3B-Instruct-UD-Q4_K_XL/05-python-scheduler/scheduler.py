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
    
    # Create list of (end_time, start_time, weight, original_index) for sorting
    indexed_jobs = [(job[1], job[0], job[2], i) for i, job in enumerate(jobs)]
    indexed_jobs.sort()  # Sort by end time
    
    # Extract sorted data
    end_times = [job[0] for job in indexed_jobs]
    start_times = [job[1] for job in indexed_jobs]
    weights = [job[2] for job in indexed_jobs]
    indices = [job[3] for job in indexed_jobs]
    
    n = len(jobs)
    
    # dp[i] represents the maximum weight achievable using jobs 0 to i
    dp = [0.0] * n
    
    # Base case
    dp[0] = weights[0]
    
    # Fill dp array
    for i in range(1, n):
        # Option 1: Don't include current job
        option1 = dp[i-1]
        
        # Option 2: Include current job
        # Find latest job that doesn't overlap with current job
        # We need the latest job with end_time <= start_time of current job
        latest_non_overlapping = _binary_search_latest_non_overlapping(end_times, start_times[i], i)
        
        if latest_non_overlapping == -1:
            # No previous job available
            option2 = weights[i]
        else:
            option2 = dp[latest_non_overlapping] + weights[i]
        
        dp[i] = max(option1, option2)
    
    # Backtrack to find the actual jobs chosen
    chosen_indices = []
    i = n - 1
    while i >= 0:
        if i == 0:
            if dp[i] > 0:
                chosen_indices.append(indices[i])
            break
        else:
            # If including current job gives better result than excluding it
            if dp[i] != dp[i-1]:
                chosen_indices.append(indices[i])
                # Find the latest non-overlapping job
                latest_non_overlapping = _binary_search_latest_non_overlapping(end_times, start_times[i], i)
                i = latest_non_overlapping
            else:
                i -= 1
    
    # Sort chosen indices by start time (and by index for ties)
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (dp[n-1], chosen_indices)


def _binary_search_latest_non_overlapping(end_times, start_time, current_index):
    """
    Find the latest job (by index) that ends at or before start_time.
    """
    left, right = 0, current_index - 1
    result = -1
    
    while left <= right:
        mid = (left + right) // 2
        if end_times[mid] <= start_time:
            result = mid
            left = mid + 1
        else:
            right = mid - 1
    
    return result
