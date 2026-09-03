import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of (start, end, weight) tuples.
        
    Returns:
        A tuple (total_weight, chosen_indices).
    """
    if not jobs:
        return (0.0, [])

    # Store original indices to return them at the end
    # indexed_jobs = [(start, end, weight, original_index)]
    indexed_jobs = []
    for i, job in enumerate(jobs):
        indexed_jobs.append((job[0], job[1], job[2], i))

    # Sort jobs by end time to apply dynamic programming
    # If end times are equal, the order doesn't strictly matter for the weight,
    # but we keep it stable.
    indexed_jobs.sort(key=lambda x: x[1])

    n = len(indexed_jobs)
    # dp[i] will store the maximum weight using a subset of the first i jobs
    dp = [0.0] * (n + 1)
    # parent[i] will store whether the i-th job (1-indexed) was included in the optimal solution for dp[i]
    # If included, parent[i] = index of the previous job used. If not, parent[i] = -1.
    # To reconstruct the path efficiently, we store the index of the previous compatible job.
    prev_compatible = [0] * (n + 1)
    included = [False] * (n + 1)

    # Extract end times for binary search
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start, end, weight, idx = indexed_jobs[i-1]
        
        # Find the latest job that ends before or at the start time of the current job.
        # bisect_right finds the insertion point to maintain order.
        # We want the largest j such that end_times[j-1] <= start.
        j = bisect.bisect_right(end_times, start)
        
        # If the current job is included, the weight is weight + dp[j]
        # If not included, the weight is dp[i-1]
        if weight + dp[j] > dp[i-1]:
            dp[i] = weight + dp[j]
            included[i] = True
            prev_compatible[i] = j
        else:
            dp[i] = dp[i-1]
            included[i] = False
            prev_compatible[i] = i - 1

    # Reconstruct the chosen indices
    chosen_indices = []
    curr = n
    while curr > 0:
        if included[curr]:
            # Add the original index of the job
            chosen_indices.append(indexed_jobs[curr-1][3])
            curr = prev_compatible[curr]
        else:
            curr = prev_compatible[curr]

    # The problem asks for indices sorted by the job's start time.
    # We have the indices, now we need to sort them based on the original jobs' start times.
    # Tie-break by index ascending.
    
    # To sort by start time, we can use the original jobs list.
    # chosen_indices currently contains indices into the original 'jobs' list.
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(dp[n]), chosen_indices)
