def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])
    
    # Create list of (start, end, weight, original_index)
    indexed_jobs = [(jobs[i][0], jobs[i][1], jobs[i][2], i) for i in range(n)]
    
    # Sort by end time, then by start time, then by index for deterministic tie-breaking
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    # Extract sorted arrays
    starts = [x[0] for x in indexed_jobs]
    ends = [x[1] for x in indexed_jobs]
    weights = [x[2] for x in indexed_jobs]
    orig_indices = [x[3] for x in indexed_jobs]
    
    # For each job i (in sorted order), find the rightmost job j such that ends[j] <= starts[i]
    # This is the last job that is compatible with job i
    # We use binary search on the ends array
    import bisect
    
    # dp[i] = max weight using jobs 0..i (inclusive) in sorted order
    # dp[i] = max(dp[i-1], weights[i] + (dp[p(i)] if p(i) >= 0 else 0))
    # where p(i) is the largest index j < i such that ends[j] <= starts[i]
    
    # We'll compute dp iteratively
    # dp[0] = weights[0]
    # For i >= 1:
    #   p = bisect_right(ends, starts[i]) - 1  # rightmost index with ends[j] <= starts[i]
    #   if p >= 0 and p < i:
    #       candidate = weights[i] + dp[p]
    #   else:
    #       candidate = weights[i]
    #   dp[i] = max(dp[i-1], candidate)
    
    # But we also need to reconstruct the solution.
    # Let's store for each i whether we took job i or not.
    # take[i] = True if we chose job i in the optimal solution for dp[i]
    
    # Actually, let's think more carefully. dp[i] is the max weight considering jobs 0..i.
    # If we take job i, the previous compatible job is at index p(i), and the value is weights[i] + (dp[p(i)] if p(i) >= 0 else 0).
    # If we don't take job i, the value is dp[i-1] (if i > 0).
    
    # For reconstruction, we can store:
    # - dp[i]: the max weight
    # - prev[i]: if we took job i, then prev[i] = p(i); if we didn't take job i, prev[i] = i-1 (meaning we just skip to i-1)
    # But this is a bit tricky. Let me use a different approach.
    
    # Let's store:
    # dp[i] = max weight for jobs 0..i
    # choice[i] = 'take' or 'skip'
    # If choice[i] == 'take', then the previous job in the chain is p(i)
    # If choice[i] == 'skip', then the previous state is i-1
    
    # Actually, a cleaner way:
    # dp[i] = max weight considering first i+1 jobs (indices 0..i)
    # For reconstruction, we can backtrack from i = n-1:
    #   If i == 0: if dp[0] == weights[0], take job 0
    #   Else:
    #     p = p(i)
    #     take_val = weights[i] + (dp[p] if p >= 0 else 0)
    #     skip_val = dp[i-1]
    #     If take_val >= skip_val (and we want to prefer taking when equal? or either is fine):
    #       Take job i, then go to p
    #     Else:
    #       Skip job i, go to i-1
    
    # But we need to be careful with floating point comparisons. Let's use >= for take preference.
    
    # Let's compute dp and also store p(i) for each i.
    
    p = [-1] * n  # p[i] = rightmost index j < i with ends[j] <= starts[i], or -1 if none
    for i in range(n):
        # Find rightmost j such that ends[j] <= starts[i]
        # bisect_right returns the insertion point, so bisect_right(ends, starts[i]) - 1 gives the rightmost index with ends[j] <= starts[i]
        pos = bisect.bisect_right(ends, starts[i]) - 1
        if pos >= 0 and pos < i:
            p[i] = pos
        else:
            p[i] = -1
    
    # Now compute dp
    dp = [0.0] * n
    dp[0] = weights[0]
    for i in range(1, n):
        take_val = weights[i]
        if p[i] >= 0:
            take_val += dp[p[i]]
        skip_val = dp[i-1]
        dp[i] = max(take_val, skip_val)
    
    # Reconstruct
    chosen = []
    i = n - 1
    while i >= 0:
        if i == 0:
            # Check if we should take job 0
            # dp[0] = weights[0], so we always "take" it in the sense that it's the only option
            # But wait, dp[0] is just weights[0]. There's no skip option for i=0.
            # So if dp[0] > 0, we take it. Since weights > 0, we always take it.
            chosen.append(orig_indices[0])
            break
        else:
            take_val = weights[i]
            if p[i] >= 0:
                take_val += dp[p[i]]
            skip_val = dp[i-1]
            if take_val >= skip_val:
                # Take job i
                chosen.append(orig_indices[i])
                i = p[i]
            else:
                # Skip job i
                i = i - 1
    
    # Sort chosen by start time, then by index
    # We need to sort by (start, index)
    # Get the start times for the chosen jobs
    chosen_with_info = [(jobs[idx][0], idx) for idx in chosen]
    chosen_with_info.sort(key=lambda x: (x[0], x[1]))
    chosen_indices = [x[1] for x in chosen_with_info]
    
    total_weight = dp[n-1]
    
    return (total_weight, chosen_indices)
