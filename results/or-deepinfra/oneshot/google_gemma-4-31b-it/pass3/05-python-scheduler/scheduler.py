import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem using Dynamic Programming 
    and Binary Search in O(n log n) time.
    """
    if not jobs:
        return (0.0, [])

    # 1. Store original indices to reconstruct the solution
    # indexed_jobs = [(start, end, weight, original_index), ...]
    indexed_jobs = []
    for i in range(len(jobs)):
        indexed_jobs.append((jobs[i][0], jobs[i][1], jobs[i][2], i))

    # 2. Sort jobs by their end times to enable DP
    # Sorting is O(n log n)
    indexed_jobs.sort(key=lambda x: x[1])

    n = len(indexed_jobs)
    # dp[i] stores the maximum weight achievable using a subset of the first i jobs
    dp = [0.0] * (n + 1)
    # parent[i] stores whether the i-th job (1-indexed) was included in the optimal solution for dp[i]
    # If True, job i-1 was included. If False, we take the value from dp[i-1].
    included = [False] * (n + 1)
    # prev_idx[i] stores the index of the last compatible job if job i-1 was included
    prev_idx = [0] * (n + 1)

    # Extract end times for binary search
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start, end, weight, idx = indexed_jobs[i-1]
        
        # Find the rightmost job that ends before or at the start time of the current job.
        # bisect_right returns the insertion point which is the index of the first 
        # element strictly greater than 'start'. Subtracting 1 gives the last element <= 'start'.
        p = bisect.bisect_right(end_times, start)
        
        # We only consider jobs that end by 'start'. 
        # Since end_times is 0-indexed, and p is the count of elements <= start,
        # the max weight from compatible jobs is dp[p].
        # However, we must ensure we don't include the current job itself if it's at index p-1.
        # Because we are iterating i from 1 to n, and p is derived from end_times,
        # and we only look at end_times[:i-1], we should cap p at i-1.
        p = min(p, i - 1)
        
        weight_with_current = weight + dp[p]
        
        if weight_with_current > dp[i-1]:
            dp[i] = weight_with_current
            included[i] = True
            prev_idx[i] = p
        else:
            dp[i] = dp[i-1]
            included[i] = False

    # 3. Backtrack to find the indices of the chosen jobs
    chosen_indices = []
    curr = n
    while curr > 0:
        if included[curr]:
            # Job at index curr-1 in sorted list was chosen
            chosen_indices.append(indexed_jobs[curr-1][3])
            curr = prev_idx[curr]
        else:
            curr -= 1

    # The problem asks for indices sorted by the job's start time.
    # We can sort the chosen indices based on the original jobs' start times.
    # Since we backtracked from the end, the indices are already roughly in reverse order of end times.
    # To be safe and strictly follow the "sorted by start time" rule:
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(dp[n]), chosen_indices)
