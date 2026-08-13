import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.

    jobs: list of (start, end, weight) tuples.
    Returns (total_weight, chosen_indices) sorted by start time.
    """
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # 1. Preprocessing: Augment jobs with original index and sort by end time.
    # job_data: list of (start, end, weight, original_index)
    job_data = []
    for i, (s, e, w) in enumerate(jobs):
        job_data.append((s, e, w, i))

    # Sort primarily by end time (e), secondarily by start time (s) for stability.
    # This sorting is crucial for the DP structure.
    job_data.sort(key=lambda x: (x[1], x[0]))

    # Extract sorted end times for efficient binary search later
    end_times = [job[1] for job in job_data]

    # 2. Finding Predecessors (p[i]):
    # p[i] will store the index (in the sorted job_data list) of the latest
    # non-overlapping job preceding job i.
    p = [-1] * n

    for i in range(n):
        start_i = job_data[i][0]
        
        # We need to find the index j < i such that job_data[j][1] <= start_i,
        # and j is maximized.
        
        # We search in the end_times array for the insertion point of start_i.
        # bisect_right finds an insertion point which comes after (to the right of)
        # any existing entries of start_i.
        # We are looking for the index of the last element <= start_i.
        
        # Search space is indices [0, i-1]
        
        # We search for the index where start_i would be inserted to maintain order.
        # We look for the index of the first job that *starts* after job i ends,
        # or equivalently, the index of the first job whose end time is > start_i.
        
        # We search in end_times[:i] for the largest index j such that end_times[j] <= start_i.
        
        # bisect_right finds insertion point k such that all a[:k] <= x and all a[k:] > x.
        # We search in end_times[:i] for start_i.
        
        # We search for the index in the full end_times array up to i-1.
        # The result 'idx' is the index *after* the last element <= start_i.
        idx = bisect.bisect_right(end_times, start_i, hi=i)
        
        if idx > 0:
            # The predecessor is at index idx - 1
            p[i] = idx - 1

    # 3. Dynamic Programming
    # dp[i] = max weight using a subset of jobs 0 through i.
    dp = [0.0] * n
    
    # Base case i=0
    dp[0] = job_data[0][2]  # weight of job 0

    for i in range(1, n):
        weight_i = job_data[i][2]
        
        # Option 1: Include job i
        weight_include = weight_i
        pred_index = p[i]
        if pred_index != -1:
            weight_include += dp[pred_index]
            
        # Option 2: Exclude job i
        weight_exclude = dp[i-1]
        
        dp[i] = max(weight_include, weight_exclude)

    total_weight = dp[n-1]

    # 4. Reconstruction
    chosen_indices_sorted = []
    
    if total_weight > 0:
        current_idx = n - 1
        while current_idx >= 0:
            # Check if job_data[current_idx] was included in the optimal solution
            
            weight_i = job_data[current_idx][2]
            pred_index = p[current_idx]
            
            # If including job current_idx leads to the current DP value, it was chosen.
            # Note: If weight_include == weight_exclude, we prefer exclusion (Option 2)
            # to ensure we find *a* valid set, but including is fine too.
            
            weight_include = weight_i
            if pred_index != -1:
                weight_include += dp[pred_index]
            
            if dp[current_idx] == weight_include:
                # Job current_idx was chosen
                original_index = job_data[current_idx][3]
                chosen_indices_sorted.append(original_index)
                current_idx = pred_index
            else:
                # Job current_idx was excluded (dp[i] == dp[i-1])
                current_idx -= 1
        
        # The reconstruction traces backwards based on the sorted order.
        # The requirement is that the output indices must be sorted by start time.
        # Since we only stored the indices of the chosen jobs, we must re-sort them
        # based on their original start times.
        
        final_jobs_info = []
        for idx in chosen_indices_sorted:
            s, _, _, _ = jobs[idx]
            final_jobs_info.append((s, idx))
            
        # Sort by start time (s), then by original index (idx) for tie-breaking
        final_jobs_info.sort(key=lambda x: (x[0], x[1]))
        
        final_indices = [idx for _, idx in final_jobs_info]
        return (total_weight, final_indices)
    else:
        return (0.0, [])

# Example verification (optional, for testing locally)
# jobs_ex = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
# result = best_schedule(jobs_ex)
# print(result) # Expected: (13.0, [2, 6])
