import bisect


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solve the weighted interval scheduling problem in O(n log n) time.
    
    Args:
        jobs: list of (start, end, weight) tuples
        
    Returns:
        (total_weight, chosen_indices) where chosen_indices are sorted by
        start time (ties broken by index ascending)
    """
    if not jobs:
        return (0.0, [])
    
    n = len(jobs)
    
    # Create a list of (start, end, weight, original_index) and sort by start time
    # For tie-breaking in start time, we use original index as secondary key
    indexed_jobs = [(jobs[i][0], jobs[i][1], jobs[i][2], i) for i in range(n)]
    indexed_jobs.sort(key=lambda x: (x[0], x[3]))
    
    # Extract sorted arrays
    starts = [j[0] for j in indexed_jobs]
    ends = [j[1] for j in indexed_jobs]
    weights = [j[2] for j in indexed_jobs]
    
    # For each job i (in sorted order), find the latest job j < i that doesn't overlap with i.
    # Job j doesn't overlap with job i if ends[j] <= starts[i].
    # We need to find the largest j < i such that ends[j] <= starts[i].
    
    # Precompute p[i] = index of the latest non-overlapping job before job i
    # Using binary search on the ends array (which is sorted by start time, not end time)
    # We need to search among jobs 0..i-1 for the one with largest index where ends[j] <= starts[i]
    
    # Since we need to search efficiently, let's think about this differently.
    # We'll use binary search. For each job i, we want the rightmost job j < i with ends[j] <= starts[i].
    
    # To make binary search work, we can maintain the ends values and search.
    # But ends array is not sorted by end time. We need a different approach.
    
    # Alternative: For binary search, we can use the fact that we're looking for
    # the latest job (by sorted order index) that ends <= starts[i].
    # We can precompute this using binary search on a separate structure.
    
    # Let's use a different approach: sort by end time for the DP, but we need to
    # be careful about the output format.
    
    # Actually, let me reconsider. The standard O(n log n) approach:
    # 1. Sort jobs by end time
    # 2. For each job, find the latest job that ends <= current job's start (binary search)
    # 3. DP: dp[i] = max weight using subset of first i jobs (sorted by end time)
    
    # Let me redo this properly.
    
    # Sort by end time, with tie-breaking by start time then index
    sorted_by_end = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))
    
    # Create arrays in end-time order
    ends_sorted = [jobs[i][1] for i in sorted_by_end]
    starts_sorted = [jobs[i][0] for i in sorted_by_end]
    weights_sorted = [jobs[i][2] for i in sorted_by_end]
    orig_idx_sorted = sorted_by_end  # orig_idx_sorted[j] = original index of j-th job in end-sorted order
    
    # For each job j in end-sorted order, find the latest job k < j (in end-sorted order)
    # such that ends_sorted[k] <= starts_sorted[j]
    # Since ends_sorted is sorted (by end time), we can binary search.
    
    # dp[j] = maximum weight considering jobs 0..j in end-sorted order
    # dp[j] = max(dp[j-1], weights_sorted[j] + dp[p[j]]) where p[j] is the largest index < j
    #          with ends_sorted[p[j]] <= starts_sorted[j]
    
    # Compute p array using binary search
    p = [-1] * n  # p[j] = index in end-sorted order, or -1 if no such job exists
    
    for j in range(n):
        # Binary search for the rightmost k < j with ends_sorted[k] <= starts_sorted[j]
        # Since ends_sorted[0..j-1] is sorted, we can use bisect_right
        target = starts_sorted[j]
        # bisect_right returns the insertion point, so the element at index (pos-1) is <= target
        pos = bisect.bisect_right(ends_sorted, target, 0, j)
        if pos > 0:
            p[j] = pos - 1
        else:
            p[j] = -1
    
    # DP
    dp = [0.0] * n
    dp[0] = weights_sorted[0]
    
    for j in range(1, n):
        include_weight = weights_sorted[j]
        if p[j] != -1:
            include_weight += dp[p[j]]
        dp[j] = max(dp[j-1], include_weight)
    
    # Reconstruct the solution
    chosen = []
    j = n - 1
    while j >= 0:
        include_weight = weights_sorted[j]
        if p[j] != -1:
            include_weight += dp[p[j]]
        if include_weight >= dp[j]:
            # Include job j
            chosen.append(orig_idx_sorted[j])
            if p[j] != -1:
                j = p[j]
            else:
                j = -1
        else:
            j -= 1
    
    # Sort chosen indices by start time (ties by index ascending)
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (dp[n-1], chosen)
