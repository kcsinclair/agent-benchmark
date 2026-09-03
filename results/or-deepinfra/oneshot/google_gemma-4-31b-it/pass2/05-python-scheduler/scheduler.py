import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of (start, end, weight) tuples.
        
    Returns:
        A tuple (total_weight, chosen_indices) where chosen_indices are the 
        indices of the jobs in the original input list.
    """
    if not jobs:
        return (0.0, [])

    n = len(jobs)
    # Store original indices to recover the subset later
    # indexed_jobs = [(start, end, weight, original_index), ...]
    indexed_jobs = []
    for i in range(n):
        s, e, w = jobs[i]
        indexed_jobs.append((s, e, w, i))

    # Sort jobs by end time to enable dynamic programming
    # O(n log n)
    indexed_jobs.sort(key=lambda x: x[1])

    # dp[i] = max weight achievable using a subset of the first i jobs
    # parent[i] = index of the previous job in the optimal sequence for dp[i]
    # used[i] = boolean, True if the i-th job (in sorted list) was included in dp[i]
    dp = [0.0] * (n + 1)
    parent = [-1] * (n + 1)
    used = [False] * (n + 1)

    # Extract end times for binary search
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start, end, weight, idx = indexed_jobs[i-1]
        
        # Find the rightmost job that ends before or at the start time of the current job.
        # bisect_right returns the insertion point which is one index past the target.
        # We want the index j such that end_times[j-1] <= start.
        prev_idx = bisect.bisect_right(end_times, start)
        
        # Option 1: Include the current job
        weight_with_current = weight + dp[prev_idx]
        
        # Option 2: Exclude the current job
        weight_without_current = dp[i-1]
        
        if weight_with_current > weight_without_current:
            dp[i] = weight_with_current
            parent[i] = prev_idx
            used[i] = True
        else:
            dp[i] = weight_without_current
            parent[i] = i - 1
            used[i] = False

    # Backtrack to find the indices of the jobs used in the optimal solution
    chosen_indices = []
    curr = n
    while curr > 0:
        if used[curr]:
            # The job at index curr-1 in the sorted list was used
            chosen_indices.append(indexed_jobs[curr-1][3])
            curr = parent[curr]
        else:
            curr = parent[curr]

    # The problem asks for indices sorted by the job's start time.
    # Since we backtracked from the end, we have them in reverse order of end times.
    # We sort them based on the original job's start time, then by original index.
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(dp[n]), chosen_indices)
