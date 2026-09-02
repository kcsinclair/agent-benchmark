import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Args:
        jobs: A list of (start, end, weight) tuples.
        
    Returns:
        A tuple (total_weight, chosen_indices) where chosen_indices are the 
        original indices of the jobs in the optimal subset, sorted by start time.
    """
    if not jobs:
        return (0.0, [])

    # We need to keep track of original indices to return them at the end.
    # indexed_jobs: list of (start, end, weight, original_index)
    indexed_jobs = []
    for i, (s, e, w) in enumerate(jobs):
        indexed_jobs.append((s, e, w, i))

    # Sort jobs by end time to facilitate dynamic programming.
    # O(n log n)
    indexed_jobs.sort(key=lambda x: x[1])

    n = len(indexed_jobs)
    
    # dp[i] will store the maximum weight achievable using a subset of 
    # the first i jobs (from the sorted list).
    # dp[0] is a dummy base case for 0 jobs.
    dp = [0.0] * (n + 1)
    
    # parent[i] will store the index of the previous job in the optimal 
    # sequence ending at job i-1, used for reconstruction.
    # If job i-1 is not included, parent[i] = i-1.
    # If job i-1 is included, parent[i] = index of the last compatible job.
    # To simplify reconstruction, we store whether the job was included.
    included = [False] * (n + 1)
    prev_job_idx = [-1] * (n + 1)

    # Extract end times for binary search
    end_times = [job[1] for job in indexed_jobs]

    for i in range(1, n + 1):
        start, end, weight, original_idx = indexed_jobs[i-1]
        
        # Find the latest job that ends before or at the current job's start time.
        # bisect_right finds the first index where end_time > start.
        # Subtracting 1 gives the index of the last job where end_time <= start.
        idx = bisect.bisect_right(end_times, start)
        
        # Note: bisect_right on end_times might return an index that points to 
        # a job that ends exactly at 'start'. However, we must ensure we don't 
        # pick the current job itself if its end time is the same as its start 
        # (though constraints say start < end). 
        # More importantly, bisect_right returns the position to insert 'start' 
        # while maintaining order. If end_times[idx-1] == start, it's compatible.
        
        # Because we are looking for the last job j < i such that end_j <= start_i,
        # and end_times is sorted, bisect_right(end_times, start) gives us the 
        # count of elements <= start.
        # Since our dp is 1-indexed, 'idx' is exactly the index we need for dp.
        
        # We must ensure idx < i to avoid using the current job to satisfy itself.
        # Since start < end, end_times[i-1] > start, so idx will always be < i.
        idx = min(idx, i - 1)

        weight_if_included = weight + dp[idx]
        weight_if_excluded = dp[i-1]

        if weight_if_included > weight_if_excluded:
            dp[i] = weight_if_included
            included[i] = True
            prev_job_idx[i] = idx
        else:
            dp[i] = weight_if_excluded
            included[i] = False
            prev_job_idx[i] = i - 1

    # Reconstruct the solution
    chosen_indices = []
    curr = n
    while curr > 0:
        if included[curr]:
            # The job at indexed_jobs[curr-1] was included
            chosen_indices.append(indexed_jobs[curr-1][3])
            curr = prev_job_idx[curr]
        else:
            # The job at indexed_jobs[curr-1] was not included
            curr = prev_job_idx[curr]

    # The problem asks for indices sorted by the job's start time.
    # Since we reconstructed backwards, we reverse and then sort by start time.
    # However, the reconstruction logic above naturally follows the DP path.
    # Let's sort the resulting indices based on the start times of the original jobs.
    
    # To satisfy "sorted by the job's start time (break ties by index ascending)":
    # We need the start times of the chosen jobs.
    chosen_jobs_info = []
    # We need to map the original indices back to their start times.
    # A dictionary is efficient for this.
    start_map = {indexed_jobs[i][3]: indexed_jobs[i][0] for i in range(n)}
    
    # Sort chosen_indices based on (start_time, original_index)
    chosen_indices.sort(key=lambda idx: (start_map[idx], idx))

    return (dp[n], chosen_indices)
