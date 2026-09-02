import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of (start, end, weight) tuples.
        
    Returns:
        A tuple (total_weight, chosen_indices) where total_weight is the maximum
        weight and chosen_indices is a list of indices of the jobs used.
    """
    if not jobs:
        return (0.0, [])

    # Store original indices to track them after sorting
    # indexed_jobs: (start, end, weight, original_index)
    indexed_jobs = []
    for i in range(len(jobs)):
        s, e, w = jobs[i]
        indexed_jobs.append((s, e, w, i))

    # Sort jobs by end time to enable dynamic programming
    # If end times are equal, the order doesn't strictly matter for correctness,
    # but we keep it stable.
    indexed_jobs.sort(key=lambda x: x[1])

    n = len(indexed_jobs)
    # dp[i] stores the maximum weight achievable using a subset of the first i jobs
    dp = [0.0] * (n + 1)
    # parent[i] stores whether the i-th job (1-indexed) was included in the optimal solution for dp[i]
    # If included, we store the index of the previous compatible job.
    parent = [0] * (n + 1)

    # Extract end times for binary search
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start, end, weight, idx = indexed_jobs[i-1]
        
        # Find the rightmost job that ends before or at the start time of the current job.
        # bisect_right finds the insertion point to maintain order.
        # Since we want end_time <= start, bisect_right on end_times gives the index
        # of the first element > start. The element before that is <= start.
        prev_idx = bisect.bisect_right(end_times, start)
        
        # We only consider jobs that end strictly before or at the start of the current job.
        # However, bisect_right might return an index that includes the current job itself
        # if the current job's end time is also <= its start time (not possible per rules)
        # or if multiple jobs have the same end time. 
        # We must ensure prev_idx < i.
        prev_idx = min(prev_idx, i - 1)
        
        # Option 1: Include the current job
        include_weight = weight + dp[prev_idx]
        
        # Option 2: Exclude the current job
        exclude_weight = dp[i-1]
        
        if include_weight > exclude_weight:
            dp[i] = include_weight
            parent[i] = prev_idx + 1 # Mark as included and store pointer to prev compatible
        else:
            dp[i] = exclude_weight
            parent[i] = -1 # Mark as excluded

    # Backtrack to find the indices of the chosen jobs
    chosen_indices = []
    curr = n
    while curr > 0:
        if parent[curr] != -1:
            # Job (curr-1) was included
            job_idx = indexed_jobs[curr-1][3]
            chosen_indices.append(job_idx)
            curr = parent[curr] - 1 # Move to the compatible job's index
            # Wait, the logic above is slightly flawed. Let's refine:
            # If parent[curr] is the index of the compatible job, 
            # we jump directly to that DP state.
            curr = parent[curr]
            # Correcting the loop:
            # If parent[curr] == -1, we didn't take job curr-1, so we check curr-1.
            # If parent[curr] != -1, we took job curr-1, and the next state is dp[parent[curr]-1]
            # No, the logic is: if we took job i, the previous state was dp[prev_idx].
            # Let's rewrite the backtracking clearly.
            break 
    
    # Redoing backtracking for clarity
    chosen_indices = []
    curr = n
    while curr > 0:
        if parent[curr] != -1:
            # Job at index curr-1 in indexed_jobs was included
            chosen_indices.append(indexed_jobs[curr-1][3])
            # Jump to the DP state of the last compatible job
            curr = parent[curr] - 1 if parent[curr] != 0 else 0
            # Wait, if parent[curr] = prev_idx + 1, then the previous state was dp[prev_idx].
            # So the next curr should be prev_idx.
            # Let's use a simpler parent array:
            # if included: parent[i] = prev_idx
            # if excluded: parent[i] = i-1
            break
    
    # Re-implementing backtracking properly
    return _backtrack(indexed_jobs, dp, parent, n)

def _backtrack(indexed_jobs, dp, parent, n):
    # Re-calculating the path based on the DP decisions
    # To avoid confusion, let's use the logic: 
    # if dp[i] == dp[i-1], we could have excluded job i-1.
    # if dp[i] == weight[i-1] + dp[prev_idx], we could have included job i-1.
    
    chosen_indices = []
    curr = n
    # We need the original start times to sort the final indices as requested
    # but the problem asks for indices sorted by the job's start time.
    
    # Re-run the DP logic slightly differently to make backtracking robust
    # Let's use a simple "included" boolean array.
    included = [False] * (n + 1)
    prev_compat = [0] * (n + 1)
    
    # Re-calculate DP to fill these arrays
    end_times = [job[1] for job in indexed_jobs]
    dp_val = [0.0] * (n + 1)
    for i in range(1, n + 1):
        start, end, weight, idx = indexed_jobs[i-1]
        prev_idx = bisect.bisect_right(end_times, start)
        prev_idx = min(prev_idx, i - 1)
        
        if weight + dp_val[prev_idx] > dp_val[i-1]:
            dp_val[i] = weight + dp_val[prev_idx]
            included[i] = True
            prev_compat[i] = prev_idx
        else:
            dp_val[i] = dp_val[i-1]
            included[i] = False
            
    curr = n
    final_indices = []
    while curr > 0:
        if included[curr]:
            final_indices.append(indexed_jobs[curr-1][3])
            curr = prev_compat[curr]
        else:
            curr -= 1
            
    # The problem asks for indices sorted by the job's start time.
    # We have the indices, now we fetch their start times from the original list.
    # However, the jobs were already sorted by end time. 
    # Let's just sort the chosen indices based on the original jobs' start times.
    # "sorted by the job's start time (break ties by index ascending)"
    
    # To do this efficiently, we can use the original jobs list.
    # But wait, the problem says "sorted by the job's start time".
    # Let's just sort the final_indices list using a key.
    
    # We need the original jobs to access start times.
    # Since we are inside a helper, we need to pass the original jobs or 
    # use the indexed_jobs we already have.
    
    # Let's use a lambda that looks up the start time and index.
    # We need the original jobs list for this.
    # Let's move this logic back into the main function.
    return dp_val[n], final_indices

# Redefining the main function to integrate the corrected backtracking
def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    if not jobs:
        return (0.0, [])

    indexed_jobs = []
    for i in range(len(jobs)):
        s, e, w = jobs[i]
        indexed_jobs.append((s, e, w, i))

    indexed_jobs.sort(key=lambda x: x[1])
    n = len(indexed_jobs)
    
    dp = [0.0] * (n + 1)
    included = [False] * (n + 1)
    prev_compat = [0] * (n + 1)
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start, end, weight, idx = indexed_jobs[i-1]
        prev_idx = bisect.bisect_right(end_times, start)
        prev_idx = min(prev_idx, i - 1)
        
        if weight + dp[prev_idx] > dp[i-1]:
            dp[i] = weight + dp[prev_idx]
            included[i] = True
            prev_compat[i] = prev_idx
        else:
            dp[i] = dp[i-1]
            included[i] = False

    chosen_indices = []
    curr = n
    while curr > 0:
        if included[curr]:
            chosen_indices.append(indexed_jobs[curr-1][3])
            curr = prev_compat[curr]
        else:
            curr -= 1
            
    # Sort chosen_indices by the start time of the job, then by index.
    # original_jobs[idx] = (start, end, weight)
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return (float(dp[n]), chosen_indices)
