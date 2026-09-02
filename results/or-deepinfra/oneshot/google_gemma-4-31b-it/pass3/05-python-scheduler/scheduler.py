import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of (start, end, weight) tuples.
        
    Returns:
        A tuple (total_weight, chosen_indices) where total_weight is the maximum
        weight and chosen_indices is the list of indices of the jobs used.
    """
    if not jobs:
        return (0.0, [])

    # 1. Store original indices and sort jobs by end time.
    # Sorting by end time is the standard approach for the DP solution.
    # indexed_jobs = [(start, end, weight, original_index), ...]
    indexed_jobs = []
    for i, job in enumerate(jobs):
        indexed_jobs.append((job[0], job[1], job[2], i))
    
    # Sort by end time ascending.
    indexed_jobs.sort(key=lambda x: x[1])

    n = len(indexed_jobs)
    # dp[i] stores the maximum weight achievable using a subset of the first i jobs.
    dp = [0.0] * (n + 1)
    # parent[i] stores whether the i-th job (1-indexed) was included in the optimal solution for dp[i].
    # If included, we store the index of the previous compatible job.
    # If not included, we store -1 to indicate we just take the value from dp[i-1].
    parent = [-1] * (n + 1)
    
    # To find the last compatible job efficiently, we keep track of the end times.
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start, end, weight, idx = indexed_jobs[i-1]
        
        # Find the rightmost job that ends before or at the start time of the current job.
        # bisect_right returns the insertion point which is (index + 1).
        # Since end_times is sorted, this finds the number of jobs that end <= start.
        prev_idx = bisect.bisect_right(end_times, start)
        
        # If we include the current job:
        weight_with_current = weight + dp[prev_idx]
        
        # If we exclude the current job:
        weight_without_current = dp[i-1]
        
        if weight_with_current > weight_without_current:
            dp[i] = weight_with_current
            parent[i] = prev_idx # Mark that we took job i and the previous state was prev_idx
        else:
            dp[i] = weight_without_current
            parent[i] = -2 # Mark that we skipped job i

    # Backtrack to find the indices of the jobs used.
    chosen_indices = []
    curr = n
    while curr > 0:
        if parent[curr] == -2:
            curr -= 1
        else:
            # Job (curr-1) was included.
            prev = parent[curr]
            chosen_indices.append(indexed_jobs[curr-1][3])
            curr = prev

    # The problem asks for indices sorted by the job's start time.
    # We need to retrieve the start times for the chosen indices to sort them.
    # However, the backtracking already gives them in reverse order of end times.
    # Since we need them sorted by start time (and then index), we sort the final list.
    
    # To sort by start time, we map the chosen indices back to their original jobs.
    # result_indices = sorted(chosen_indices, key=lambda idx: (jobs[idx][0], idx))
    
    # The prompt says: "sorted by the job's start time (break ties by index ascending)".
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(dp[n]), chosen_indices)
