import bis

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Finds the maximum weight subset of non-overlapping jobs using Dynamic Programming
    optimized with binary search (O(N log N)).

    Args:
        jobs: A list of (start, end, weight) tuples.

    Returns:
        A tuple (total_weight, chosen_indices) where chosen_indices are sorted by start time.
    """
    N = len(jobs)
    if N == 0:
        return (0.0, [])

    # 1. Augment jobs with their original indices and sort them by end time.
    # Sorting by end time is crucial for the DP structure.
    # Structure: (end, start, weight, original_index)
    indexed_jobs = []
    for i, (start, end, weight) in enumerate(jobs):
        indexed_jobs.append((end, start, weight, i))
    
    # Sort primarily by end time. If end times are equal, sorting by start time 
    # or index doesn't strictly matter for correctness, but consistency helps.
    indexed_jobs.sort()

    # Extract sorted end times for binary search
    end_times = [job[0] for job in indexed_jobs]

    # 2. Dynamic Programming Setup
    # dp[i] stores the maximum weight achievable using a subset of the first i+1 jobs (0 to i)
    # in the sorted list.
    dp = [0.0] * N
    
    # parent[i] stores the index of the job that was chosen immediately before job i 
    # in the optimal schedule leading to dp[i]. This is used for reconstruction.
    parent = [-1] * N

    # 3. DP Calculation
    for i in range(N):
        end_i, start_i, weight_i, _ = indexed_jobs[i]
        
        # Case 1: Include job i
        # We need to find the latest job j < i such that job j is compatible with job i.
        # Compatibility: end_j <= start_i
        
        # We search in the end_times array (which corresponds to jobs 0 to i-1)
        # for the rightmost end time <= start_i.
        
        # bis.bisect_right finds an insertion point 'k' such that all end_times[:k] <= start_i.
        # Since we are looking for the *last* compatible job, we use bisect_right on the 
        # prefix up to i, and then step back one index.
        
        # Search space is jobs 0 to i-1.
        # We look for the index of the first element strictly greater than start_i.
        # The index before that is the last element <= start_i.
        
        # bisect_right returns the insertion point. If we search in end_times[:i], 
        # the index returned is the count of elements <= start_i.
        
        # Example: end_times[:i] = [2, 4, 6]. start_i = 5. bisect_right returns 2.
        # This means jobs 0 and 1 are compatible. The last one is at index 1.
        
        # We search in the prefix of end_times up to i (exclusive)
        j_idx_in_prefix = bis.bisect_right(end_times, start_i, hi=i)
        
        # j_idx_in_prefix is the count of compatible jobs (0-indexed).
        # The index of the best preceding job is j_idx_in_prefix - 1.
        
        prev_dp_weight = 0.0
        prev_job_index = -1
        
        if j_idx_in_prefix > 0:
            # The best preceding schedule ends at index j_idx_in_prefix - 1
            prev_dp_weight = dp[j_idx_in_prefix - 1]
            # We don't strictly need the index of the job itself, just the DP value.
            # However, for reconstruction, we need to know which job led to dp[j_idx_in_prefix - 1].
            # A simpler reconstruction method is to store the predecessor index in the DP state,
            # but since we only need *one* optimal set, we can rely on the fact that if we pick job i,
            # the optimal set is {i} U OptimalSet(j_idx_in_prefix - 1).
            pass

        weight_including_i = weight_i + prev_dp_weight
        
        # Case 2: Exclude job i
        weight_excluding_i = dp[i-1] if i > 0 else 0.0
        
        # Decision: Take the maximum
        if weight_including_i >= weight_excluding_i:
            dp[i] = weight_including_i
            # If we include job i, its predecessor is the optimal solution up to j_idx_in_prefix - 1
            # We store the index of the job that *precedes* job i in the sorted list.
            parent[i] = j_idx_in_prefix - 1
        else:
            dp[i] = weight_excluding_i
            # If we exclude job i, the predecessor is the optimal solution up to i-1
            parent[i] = i - 1

    # 4. Reconstruction
    total_weight = dp[N-1]
    chosen_indices_sorted = []
    
    # Backtrack from the last job in the sorted list (N-1)
    current_idx = N - 1
    
    # We need to find the actual set of chosen jobs. The parent array stores the index 
    # in the *sorted* list that leads to the optimal solution at the current step.
    
    # A simpler reconstruction approach:
    # If dp[i] > dp[i-1], it means job i was included in the optimal solution for dp[i].
    # If dp[i] == dp[i-1], job i was excluded.
    
    chosen_sorted_indices = []
    for i in range(N):
        # Check if job i was included in the optimal solution for dp[i]
        # If dp[i] > dp[i-1] (or if i=0 and dp[0] > 0), job i was chosen.
        
        # Note: If dp[i] == dp[i-1], job i was excluded.
        # If dp[i] == weight_including_i, job i was chosen.
        
        # We must check the condition that led to dp[i] being set to weight_including_i
        
        end_i, start_i, weight_i, original_index_i = indexed_jobs[i]
        
        # Recalculate the weight if job i is included
        j_idx_in_prefix = bis.bisect_right(end_times, start_i, hi=i)
        prev_dp_weight = dp[j_idx_in_prefix - 1] if j_idx_in_prefix > 0 else 0.0
        weight_including_i = weight_i + prev_dp_weight
        
        weight_excluding_i = dp[i-1] if i > 0 else 0.0
        
        # If the optimal value at i matches the value achieved by including job i, we include it.
        # We use >= to handle cases where both paths yield the same weight, favoring inclusion 
        # if it leads to a valid path, though the problem allows any optimal set.
        if dp[i] == weight_including_i and dp[i] > weight_excluding_i:
            chosen_sorted_indices.append(original_index_i)
        elif dp[i] == weight_including_i and dp[i] == weight_excluding_i:
            # Tie-breaker: If weights are equal, we prefer the path that includes the job 
            # if it helps satisfy the tie-breaking rule for the final output (start time, then index).
            # Since we are iterating in end-time order, this is complex. 
            # A simpler heuristic: if they are equal, we assume the exclusion path (dp[i-1]) 
            # is sufficient unless the inclusion path is strictly better or required.
            # For simplicity and correctness based on the DP structure, we only include if 
            # the inclusion path is strictly better or if the exclusion path is impossible (i=0).
            if i == 0:
                 chosen_sorted_indices.append(original_index_i)
            # If dp[i] == dp[i-1], we skip job i.
            pass
        elif dp[i] == weight_excluding_i and dp[i] > 0:
            # Job i was excluded
            pass
        elif i == 0 and dp[0] > 0:
            # Base case: Job 0 was chosen
            chosen_sorted_indices.append(original_index_i)


    # The reconstruction above is tricky due to the tie-breaking requirement on the *output* indices.
    # Let's use the standard backtracking approach based on the parent array, which is cleaner.
    
    # Reset reconstruction using the parent array logic (which tracks the predecessor in the sorted list)
    chosen_original_indices = []
    current_i = N - 1
    
    # We need a way to know if job i *was* chosen to reach dp[i].
    # If dp[i] > dp[i-1], job i must have been chosen.
    # If dp[i] == dp[i-1], job i was skipped.
    
    for i in range(N):
        end_i, start_i, weight_i, original_index_i = indexed_jobs[i]
        
        j_idx_in_prefix = bis.bisect_right(end_times, start_i, hi=i)
        prev_dp_weight = dp[j_idx_in_prefix - 1] if j_idx_in_prefix > 0 else 0.0
        weight_including_i = weight_i + prev_dp_weight
        weight_excluding_i = dp[i-1] if i > 0 else 0.0
        
        # If including job i yields the maximum weight, we mark it as chosen.
        # We use >= to favor inclusion in case of a tie, which is acceptable.
        if dp[i] == weight_including_i and dp[i] >= weight_excluding_i:
            # Job i was chosen.
            chosen_original_indices.append(original_index_i)
        # If dp[i] == weight_excluding_i and dp[i] > weight_including_i, job i was skipped.
        # If dp[i] == weight_including_i and dp[i] == weight_excluding_i, we chose to skip it 
        # (by not adding it to the list), which is valid.

    # 5. Final Formatting
    # Sort the chosen indices based on the original job start times.
    # We need the original jobs list to sort them correctly.
    
    # Create a list of (start_time, original_index) for the chosen jobs
    final_selection = []
    for idx in chosen_original_indices:
        start, end, weight = jobs[idx]
        final_selection.append((start, idx))
        
    # Sort by start time, then by index (tie-breaker)
    final_selection.sort()
    
    result_indices = [idx for start, idx in final_selection]
    
    return (total_weight, result_indices)
