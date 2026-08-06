def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Choose a subset of non-overlapping jobs to maximize total weight.
    
    Args:
        jobs: list of (start, end, weight) tuples
    
    Returns:
        (total_weight, chosen_indices) where chosen_indices are indices
        of selected jobs sorted by start time.
    """
    if not jobs:
        return (0.0, [])

    # Sort jobs by start time (and by index if start times are equal)
    indexed_jobs = [(start, end, weight, i) for i, (start, end, weight) in enumerate(jobs)]
    indexed_jobs.sort(key=lambda x: (x[0], x[3]))

    n = len(indexed_jobs)
    # dp[i] will store the maximum weight achievable considering first i jobs
    dp = [0.0] * (n + 1)
    # parent[i] will store the index of the last job chosen before job i
    parent = [-1] * (n + 1)

    # Precompute the rightmost job that ends before or at the start of job i
    # This is needed to find the latest non-overlapping job
    for i in range(n):
        start_i, end_i, weight_i, idx_i = indexed_jobs[i]
        # Find the latest job that ends before or at start_i
        # We'll use binary search for efficiency
        left, right = 0, i
        last_non_overlapping = -1
        while left <= right:
            mid = (left + right) // 2
            start_mid, end_mid, weight_mid, idx_mid = indexed_jobs[mid]
            if end_mid <= start_i:
                last_non_overlapping = mid
                left = mid + 1
            else:
                right = mid - 1
        
        # Update dp[i+1]
        dp[i + 1] = dp[i]  # Don't take job i
        if last_non_overlapping != -1:
            # Take job i and add its weight to the best solution up to last_non_overlapping
            dp[i + 1] = max(dp[i + 1], dp[last_non_overlapping + 1] + weight_i)
        else:
            # No non-overlapping job before i, so just take job i
            dp[i + 1] = max(dp[i + 1], weight_i)
        
        # Update parent for backtracking
        if last_non_overlapping != -1:
            if dp[last_non_overlapping + 1] + weight_i > dp[i + 1] - weight_i:
                parent[i + 1] = last_non_overlapping + 1
        else:
            parent[i + 1] = i

    # Backtrack to find the chosen indices
    chosen_indices = []
    i = n
    while i > 0:
        chosen_indices.append(indexed_jobs[i - 1][3])  # Add the index of the job
        i = parent[i]

    chosen_indices.reverse()

    return (dp[n], chosen_indices)
