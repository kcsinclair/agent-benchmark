import bisect

def best_schedule(jobs):
    """Weighted interval scheduling.
    
    Args:
        jobs: List of (start, end, weight) tuples.
        
    Returns:
        Tuple (total_weight, chosen_indices) where total_weight is the maximum
        achievable weight (float) and chosen_indices are the original indices
        of the selected jobs, sorted by start time (ties broken by index).
    """
    if not jobs:
        return (0.0, [])
    
    # Keep original indices
    indexed = list(enumerate(jobs))  # (orig_idx, (start, end, weight))
    # Sort by end time
    indexed.sort(key=lambda x: x[1][1])
    
    # Extract sorted fields
    orig_idx = [i for i, _ in indexed]
    starts = [s for _, (s, _, _) in indexed]
    ends = [e for _, (_, e, _) in indexed]
    weights = [w for _, (_, _, w) in indexed]
    
    n = len(jobs)
    dp = [0.0] * n          # best weight for prefix ending at i
    take = [False] * n      # whether job i is taken in optimal solution
    pred = [-1] * n         # predecessor index in sorted order when taken
    
    # Base case
    dp[0] = weights[0]
    take[0] = True
    pred[0] = -1
    
    # Fill DP table
    for i in range(1, n):
        # Find rightmost job that finishes <= start_i
        pos = bisect.bisect_right(ends, starts[i], 0, i)
        p = pos - 1
        
        include = weights[i] + (dp[p] if p != -1 else 0.0)
        if include > dp[i-1]:
            dp[i] = include
            take[i] = True
            pred[i] = p
        else:
            dp[i] = dp[i-1]
            take[i] = False
            pred[i] = -1
    
    # Reconstruct chosen indices
    chosen = []
    i = n - 1
    while i >= 0:
        if take[i]:
            chosen.append(orig_idx[i])
            i = pred[i]
        else:
            i -= 1
    
    # Sort by start time, then by original index to break ties
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (float(dp[-1]), chosen)
