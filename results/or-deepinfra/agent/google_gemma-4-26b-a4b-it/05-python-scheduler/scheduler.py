from bisect import bisect_right

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
        return 0.0, []

    n = len(jobs)
    # Store as (end, start, weight, original_index)
    indexed_jobs = []
    for i in range(n):
        s, e, w = jobs[i]
        indexed_jobs.append((e, s, w, i))

    # Sort jobs by end time
    indexed_jobs.sort()

    # ends list for binary search
    ends = [job[0] for job in indexed_jobs]
    
    dp_weight = [0.0] * (n + 1)
    included = [False] * (n + 1)
    # prev_compatible[i] stores the index j < i such that job j-1 is the 
    # last compatible job before job i-1.
    prev_compatible = [0] * (n + 1)

    for i in range(1, n + 1):
        e_i, s_i, w_i, idx_i = indexed_jobs[i-1]
        
        # Find the largest j < i such that indexed_jobs[j-1].end <= s_i
        # bisect_right returns the index where s_i could be inserted while maintaining order.
        # The index returned is the number of elements <= s_i.
        j = bisect_right(ends, s_i)
        
        # Since s_i < e_i and ends is sorted, j will always be <= i-1.
        # However, we must ensure j is not i.
        if j > i - 1:
            j = i - 1
        
        weight_if_included = w_i + dp_weight[j]
        weight_if_excluded = dp_weight[i-1]
        
        if weight_if_included > weight_if_excluded:
            dp_weight[i] = weight_if_included
            included[i] = True
            prev_compatible[i] = j
        else:
            dp_weight[i] = weight_if_excluded
            included[i] = False

    # Reconstruct the solution
    chosen_indices = []
    curr = n
    while curr > 0:
        if included[curr]:
            # Job indexed_jobs[curr-1] was included
            chosen_indices.append(indexed_jobs[curr-1][3])
            curr = prev_compatible[curr]
        else:
            # Job indexed_jobs[curr-1] was not included
            curr -= 1
            
    # Sort the chosen indices based on the job's start time (break ties by index ascending).
    chosen_indices.sort(key=lambda idx: (jobs[idx][0], idx))
    
    return float(dp_weight[n]), chosen_indices
