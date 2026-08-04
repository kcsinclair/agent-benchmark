import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of tuples (start, end, weight).
        
    Returns:
        A tuple (total_weight, chosen_indices) where chosen_indices is a list
        of indices into the original jobs list, sorted by start time.
    """
    if not jobs:
        return 0.0, []

    # We need to keep track of original indices to return them.
    # Each element: (end, start, weight, original_index)
    indexed_jobs = []
    for i, (s, e, w) in enumerate(jobs):
        indexed_jobs.append((e, s, w, i))

    # Sort jobs by end time to facilitate dynamic programming.
    indexed_jobs.sort()

    n = len(indexed_jobs)
    # dp[i] will store the maximum weight using a subset of the first i jobs.
    dp = [0.0] * (n + 1)
    # parent[i] will store the index of the previous job in the optimal subset ending at i.
    # We use -1 to indicate no previous job.
    parent = [-1] * (n + 1)
    # To reconstruct the path, we need to know if job i was included in dp[i].
    # included[i] = True if job i was part of the optimal solution for dp[i].
    included = [False] * (n + 1)

    # Extract end times for binary search
    end_times = [job[0] for job in indexed_jobs]

    for i in range(1, n + 1):
        curr_end, curr_start, curr_weight, curr_idx = indexed_jobs[i-1]
        
        # Find the latest job that ends before or at the current job's start time.
        # bisect_right finds the insertion point for curr_start in end_times.
        # Since we want end_time <= curr_start, bisect_right gives us the index
        # after the last element <= curr_start.
        idx = bisect.bisect_right(end_times, curr_start)
        
        # Option 1: Include the current job
        weight_if_included = curr_weight + dp[idx]
        
        # Option 2: Exclude the current job
        weight_if_excluded = dp[i-1]
        
        if weight_if_included > weight_if_excluded:
            dp[i] = weight_if_included
            parent[i] = idx # The job we jump back to
            included[i] = True
        else:
            dp[i] = weight_if_excluded
            parent[i] = i - 1 # We just carry over the previous DP state
            included[i] = False

    # Reconstruct the solution
    chosen_indices = []
    curr = n
    while curr > 0:
        if included[curr]:
            # The job at indexed_jobs[curr-1] was included.
            # Its original index is indexed_jobs[curr-1][3].
            chosen_indices.append(indexed_jobs[curr-1][3])
            # Move to the job that was compatible with this one.
            curr = parent[curr]
        else:
            # The job at indexed_jobs[curr-1] was not included.
            # Move to the previous DP state.
            curr = parent[curr]

    # The problem asks for indices sorted by start time.
    # Since we collected them by traversing backwards from the end, 
    # they are currently in reverse order of end times.
    # However, the requirement is "sorted by the job's start time".
    # Let's sort them based on the actual start times from the original jobs list.
    
    # To be safe and efficient, we'll sort the collected indices using the original start times.
    # We need to map index -> start_time.
    start_times_map = [jobs[i][0] for i in range(len(jobs))]
    chosen_indices.sort(key=lambda idx: (start_times_map[idx], idx))

    return dp[n], chosen_indices
