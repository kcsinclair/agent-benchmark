import bisect

def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    if not jobs:
        return (0.0, [])

    # Sort jobs by end time
    jobs_sorted = sorted(jobs, key=lambda x: x[1])
    n = len(jobs_sorted)
    end_times = [job[1] for job in jobs_sorted]

    # Precompute p[j] for each job j (0-based index)
    p = [0] * n
    for j in range(n):
        # Find the latest job that ends before or at jobs_sorted[j][0]
        start_j = jobs_sorted[j][0]
        # Use bisect_right to find insertion point of start_j in end_times
        # This gives the index of the first end time > start_j
        # So the latest job with end <= start_j is at index idx-1
        idx = bisect.bisect_right(end_times, start_j)
        p[j] = idx - 1  # -1 if no such job

    # Dynamic programming arrays
    # dp[j] = max weight for jobs 0..j
    # prev[j] = predecessor job index for optimal solution up to j
    dp = [0.0] * n
    prev = [-1] * n

    dp[0] = jobs_sorted[0][2]  # weight of first job

    for j in range(1, n):
        current_weight = jobs_sorted[j][2]
        # Option 1: include job j
        if p[j] >= 0:
            option1 = dp[p[j]] + current_weight
        else:
            option1 = current_weight  # only job j if no predecessors

        # Option 2: exclude job j
        option2 = dp[j-1]

        if option1 > option2:
            dp[j] = option1
            prev[j] = p[j]
        else:
            dp[j] = option2
            prev[j] = j-1  # predecessor is previous job

    max_weight = dp[-1]
    # Reconstruct the chosen indices
    chosen_indices = []
    current = n-1  # start from last job
    while current != -1:
        chosen_indices.append(current)
        current = prev[current]

    # Sort chosen_indices by start time (and then by index)
    # Since jobs_sorted is sorted by end time, and we reconstruct in reverse,
    # we need to sort by start time and then by original index.
    # We'll store (start_time, original_index, current_index) for sorting
    # Then extract original indices
    sorted_chosen = sorted(
        [(jobs_sorted[i][0], i, idx) for idx, i in enumerate(chosen_indices)],
        key=lambda x: (x[0], x[1])
    )
    chosen_indices_sorted = [x[1] for x in sorted_chosen]

    return (max_weight, chosen_indices_sorted)
