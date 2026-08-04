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
    indexed_jobs.sort(key=lambda x: x[1])

    n = len(indexed_jobs)
    # dp[i] will store the maximum weight using a subset of the first i jobs
    dp = [0.0] * (n + 1)
    # took_job[i] will store whether the i-th job (1-indexed) was included in the optimal solution for dp[i]
    took_job = [False] * (n + 1)
    # prev_idx[i] stores the index of the last compatible job before job i
    prev_idx = [0] * (n + 1)

    # Extract sorted end times for binary search
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start, end, weight, idx = indexed_jobs[i-1]
        
        # Find the rightmost job that ends before or at the start time of the current job.
        # bisect_right finds the insertion point to maintain order.
        # We want the largest j such that end_times[j-1] <= start.
        j = bisect.bisect_right(end_times, start)
        
        # Since end_times is sorted, bisect_right gives the index after the last element <= start.
        # However, we must be careful: the current job i is at index i-1 in indexed_jobs.
        # We only care about jobs that end before or at 'start'.
        # The jobs are indexed 0 to n-1. The dp is 1-indexed.
        # If bisect_right returns j, then end_times[0...j-1] are all <= start.
        # But we must ensure we don't pick the current job itself or any job after it.
        # Since we sorted by end time and start < end, any job ending <= start must come before job i.
        # So j will naturally be <= i-1.
        
        # Correct j for dp:
        # If j = 0, no job ends before start.
        # If j > 0, jobs at indices 0...j-1 end <= start.
        # The max weight using these is dp[j].
        
        # To handle the case where multiple jobs have the same end time, 
        # bisect_right is correct because it finds the rightmost possible index.
        # However, we must ensure j <= i-1.
        if j > i - 1:
            j = i - 1
            
        prev_idx[i] = j
        
        # Option 1: Include job i
        include_weight = weight + dp[j]
        # Option 2: Exclude job i
        exclude_weight = dp[i-1]
        
        if include_weight > exclude_weight:
            dp[i] = include_weight
            took_job[i] = True
        else:
            dp[i] = exclude_weight
            took_job[i] = False

    # Reconstruct the chosen indices
    chosen_indices = []
    curr = n
    while curr > 0:
        if took_job[curr]:
            _, _, _, original_idx = indexed_jobs[curr-1]
            chosen_indices.append(original_idx)
            curr = prev_idx[curr]
        else:
            curr -= 1

    # The problem asks for indices sorted by the job's start time, then by index ascending.
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(dp[n]), chosen_indices)
