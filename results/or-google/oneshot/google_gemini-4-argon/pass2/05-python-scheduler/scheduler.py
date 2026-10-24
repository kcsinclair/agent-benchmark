# scheduler.py
from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Solves the Weighted Interval Scheduling problem in O(n log n) time.
    
    Parameters:
        jobs: A list of (start, end, weight) tuples.
        
    Returns:
        A tuple (total_weight, chosen_indices) where total_weight is the maximum
        achievable weight (as a float) and chosen_indices is a list of original
        indices of the chosen jobs sorted by start time (and then by index).
    """
    n = len(jobs)
    if n == 0:
        return 0.0, []

    # Sort jobs by end time ascending, then start time ascending, then original index.
    # Storing tuples of (end, start, weight, original_index).
    sorted_jobs = sorted(
        (job[1], job[0], float(job[2]), i) for i, job in enumerate(jobs)
    )

    # Extract end times into a dedicated list for fast binary searching.
    ends = [job[0] for job in sorted_jobs]

    # dp[i] stores the maximum weight achievable using a subset of the first i sorted jobs.
    # dp has length n + 1, with dp[0] = 0.0 representing the base case (0 jobs).
    dp = [0.0] * (n + 1)
    
    # p[i] stores the 1-based index in sorted_jobs of the latest job that finishes
    # at or before sorted_jobs[i-1] starts (0 if no such job exists).
    p = [0] * (n + 1)

    # Bottom-up iterative DP
    for i in range(1, n + 1):
        _, start, weight, _ = sorted_jobs[i - 1]
        
        # Find the number of jobs with end_time <= start.
        # Since ends[0 : i-1] are all <= ends[i-1] and start < ends[i-1],
        # bisect_right on the full `ends` list is guaranteed to return an index <= i - 1.
        prev_idx = bisect_right(ends, start, 0, i - 1)
        p[i] = prev_idx

        take = weight + dp[prev_idx]
        skip = dp[i - 1]

        if take > skip:
            dp[i] = take
        else:
            dp[i] = skip

    # Backtrack iteratively to reconstruct the chosen subset of jobs
    chosen = []
    curr = n
    while curr > 0:
        _, _, weight, orig_idx = sorted_jobs[curr - 1]
        # If dp[curr] is strictly greater than dp[curr - 1], job curr-1 was definitely taken.
        # (Even with floating-point weights, dp[curr] was assigned directly from either
        # dp[curr - 1] or `weight + dp[p[curr]]`, so exact equality comparison with dp[curr - 1] is safe).
        if dp[curr] > dp[curr - 1]:
            chosen.append(orig_idx)
            curr = p[curr]
        else:
            curr -= 1

    # Ensure chosen indices are sorted by start time, breaking ties by original index ascending.
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return float(dp[n]), chosen
