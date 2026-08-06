def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    if not jobs:
        return (0.0, [])
    
    n = len(jobs)
    # Create list of (start, end, weight, original_index)
    indexed_jobs = [(jobs[i][0], jobs[i][1], jobs[i][2], i) for i in range(n)]
    
    # Sort by start time, then by original index (for tie-breaking)
    indexed_jobs.sort(key=lambda x: (x[0], x[3]))
    
    # Create array to store the maximum weight achievable up to each job
    dp = [0.0] * n
    prev_job = [-1] * n  # prev_job[i] stores the index of the last job that is compatible with job i
    
    # For each job, find the latest non-overlapping job
    for i in range(n):
        start_i, end_i, weight_i, orig_idx_i = indexed_jobs[i]
        
        # Find the latest job that ends before or at start_i
        left = 0
        right = i
        best_prev = -1
        
        while left <= right:
            mid = (left + right) // 2
            start_mid, end_mid, weight_mid, orig_idx_mid = indexed_jobs[mid]
            
            if end_mid <= start_i:
                best_prev = mid
                left = mid + 1
            else:
                right = mid - 1
        
        # If we found a compatible job, we can use it
        if best_prev != -1:
            dp[i] = dp[best_prev] + weight_i
            prev_job[i] = best_prev
        else:
            dp[i] = weight_i
            prev_job[i] = -1
    
    # Find the job with maximum weight
    max_weight = max(dp)
    max_idx = dp.index(max_weight)
    
    # Reconstruct the solution
    chosen_indices = []
    current = max_idx
    while current != -1:
        chosen_indices.append(indexed_jobs[current][3])
        current = prev_job[current]
    
    # Sort by start time (which should already be sorted due to our initial sort)
    # But we need to ensure the output is sorted by start time, break ties by index
    chosen_indices.sort(key=lambda x: (indexed_jobs[x][0], x))
    
    return (max_weight, chosen_indices)
