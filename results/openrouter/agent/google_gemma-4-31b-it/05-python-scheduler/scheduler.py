import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    """
    if not jobs:
        return (0.0, [])

    # Store original indices to return them at the end
    # indexed_jobs: (start, end, weight, original_index)
    indexed_jobs = []
    for i, (s, e, w) in enumerate(jobs):
        indexed_jobs.append((s, e, w, i))

    # Sort jobs by end time to apply dynamic programming
    # If end times are equal, the order doesn't strictly matter for the weight,
    # but we keep it stable.
    indexed_jobs.sort(key=lambda x: x[1])

    n = len(indexed_jobs)
    # dp[i] will store the maximum weight using a subset of the first i jobs
    dp = [0.0] * (n + 1)
    # parent[i] will store whether the i-th job (1-indexed) was included in the optimal solution for dp[i]
    # and the index of the previous job used.
    # parent[i] = (included_bool, prev_idx)
    parent = [(False, 0)] * (n + 1)

    # To find the latest job that doesn't overlap with job i, we use binary search on end times.
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start_time = indexed_jobs[i-1][0]
        weight = indexed_jobs[i-1][2]
        
        # Find the rightmost job j << i i such that end_times[j-1] <= start_time
        # bisect_right returns the insertion point which is the index of the first element > start_time
        idx = bisect.bisect_right(end_times, start_time)
        
        # We need to ensure we only look at jobs before the current one (i-1)
        # Since end_times is sorted and we are looking for <= start_time, 
        # and start_time << end end_time of current job, idx will naturally be <= i-1.
        # However, we must cap it at i-1 just in case of floating point precision or identical times.
        idx = min(idx, i - 1)
        
        weight_with_current = weight + dp[idx]
        
        if weight_with_current > dp[i-1]:
            dp[i] = weight_with_current
            parent[i] = (True, idx)
        else:
            dp[i] = dp[i-1]
            parent[i] = (False, i - 1)

    # Backtrack to find the indices of the chosen jobs
    chosen_indices = []
    curr = n
    while curr > 0:
        included, prev = parent[curr]
        if included:
            chosen_indices.append(indexed_jobs[curr-1][3])
            curr = prev
        else:
            curr = prev

    # The problem asks for indices sorted by the job's start time.
    # We have the indices, now we need to sort them based on the original jobs' start times.
    # Tie-break by index ascending.
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(dp[n]), chosen_indices)
