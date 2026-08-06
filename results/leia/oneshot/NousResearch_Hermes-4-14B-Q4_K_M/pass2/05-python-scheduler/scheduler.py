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
        # This gives the index of the first element > start_j
        # So the last element <= start_j is at index pos-1
        pos = bisect.bisect_right(end_times, start_j)
        p[j] = pos - 1  # -1 if no such job

    # Dynamic programming arrays
    # dp[j] = max weight for jobs 0..j
    # prev[j] = predecessor job index for optimal solution up to j
    dp = [0.0] * n
    prev = [-1] * n

    dp[0] = jobs_sorted[0][2]  # weight of first job

    for j in range(1, n):
        # Option 1: include jobs_sorted[j]
        weight_j = jobs_sorted[j][2]
        # Find the latest compatible job using p[j]
        if p[j] >= 0:
            weight_with_j = dp[p[j]] + weight_j
        else:
            weight_with_j = weight_j

        # Option 2: exclude jobs_sorted[j]
        weight_without_j = dp[j-1]

        if weight_with_j > weight_without_j:
            dp[j] = weight_with_j
            prev[j] = p[j]  # predecessor is p[j]
        else:
            dp[j] = weight_without_j
            prev[j] = j-1   # predecessor is j-1

    max_weight = dp[n-1]
    # Reconstruct the chosen indices
    chosen_indices = []
    current = n-1
    while current != -1:
        chosen_indices.append(current)
        current = prev[current]

    # Sort chosen_indices by start time (and then by index if needed)
    # Since jobs_sorted is sorted by end time, and we reconstruct from dp,
    # the chosen_indices are already in order of increasing end time.
    # However, the problem requires them sorted by start time (and then index).
    # Since jobs_sorted is sorted by end time, and start times are not necessarily unique,
    # we need to sort by start time and then by original index.
    # We need to map back to original indices.
    # Store (start, original_index) for each job in jobs_sorted
    # We'll create a list of tuples (start, original_index, end, weight)
    # for jobs_sorted, then sort this list by start and original_index.
    # But we already have the chosen_indices in jobs_sorted order.
    # Let's create a list of (start, original_index) for jobs_sorted.
    # Then, we can sort the chosen_indices based on these values.
    # However, since jobs_sorted is sorted by end time, and we need to sort by start time,
    # we need to extract the start times and original indices for the chosen jobs.
    # We'll create a list of (start, original_index) for all jobs_sorted.
    # Then, for the chosen_indices list (which are indices in jobs_sorted),
    # we can sort them based on the start time and original index.
    # Let's create a list of (start, original_index) for jobs_sorted.
    # We can do this by iterating through jobs_sorted and storing these values.
    # Since jobs_sorted is already sorted by end time, we can precompute this list.
    # Let's create a list `sorted_job_info` where each element is (start, original_index)
    # for jobs_sorted.
    sorted_job_info = []
    for idx, job in enumerate(jobs_sorted):
        sorted_job_info.append((job[0], idx))  # original index in jobs_sorted

    # Now, sort the chosen_indices list based on the start time and original index
    # from sorted_job_info.
    # We can do this by creating a list of tuples (start, original_index, jobs_sorted_index)
    # for the chosen jobs, then sorting by start and original_index.
    # Then extract the jobs_sorted_index.
    chosen_with_info = []
    for idx in chosen_indices:
        start, original_idx = sorted_job_info[idx]
        chosen_with_info.append((start, original_idx, idx))

    # Sort chosen_with_info by start, then by original_idx (ascending)
    chosen_with_info.sort(key=lambda x: (x[0], x[1]))

    # Extract the jobs_sorted indices in the sorted order
    sorted_chosen_indices = [x[2] for x in chosen_with_info]

    # Now, map these jobs_sorted indices back to the original input list indices.
    # We need to know the original index of each job in jobs_sorted.
    # We can create a list `original_indices` where original_indices[i] is the
    # original index of jobs_sorted[i] in the input list.
    original_indices = []
    for i, job in enumerate(jobs_sorted):
        # Find the original index of this job in the input list
        # Since jobs_sorted is a sorted version of jobs, we need to find the index
        # of job in the original jobs list.
        # However, jobs_sorted is a sorted list of tuples, and jobs is the original list.
        # We can find the index by checking for equality.
        # But this is O(n) per job, which is O(n^2) overall. This is not efficient.
        # Instead, we can precompute a list of original indices for jobs_sorted.
        # We can do this by iterating through jobs and jobs_sorted.
        # Let's create a list `original_indices` where original_indices[i] is the
        # index of jobs_sorted[i] in the original jobs list.
        # We can do this by:
        #   for i, job in enumerate(jobs_sorted):
        #       original_indices[i] = jobs.index(job)
        # But this is O(n^2) in the worst case (if all jobs are identical).
        # This is not acceptable for n=200,000.
        # Alternative: when we sort jobs_sorted, we can keep track of the original indices.
        # Let's re-sort jobs_sorted while keeping track of original indices.
        # We'll create a list of tuples (end, start, weight, original_index) for jobs.
        # Then sort by end, then by start, then by original_index.
        # This way, we can get the original indices correctly.
        # We need to redo the sorting step to include original indices.
        # Let's refactor the initial sorting step to include original indices.
        # This is a critical point. The current code does not track original indices.
        # We need to track the original indices throughout.

    # Refactoring: Track original indices throughout
    # Let's re-sort jobs_sorted while keeping track of original indices.
    # Create a list of tuples (end, start, weight, original_index) for each job.
    jobs_with_indices = [(job[1], job[0], job[2], i) for i, job in enumerate(jobs)]
    # Sort by end, then by start, then by original_index
    jobs_with_indices.sort(key=lambda x: (x[0], x[1], x[3]))
    # Now, jobs_with_indices is sorted by end, then start, then original index.
    # Extract the sorted jobs and their original indices.
    jobs_sorted = [job[1:4] for job in jobs_with_indices]  # (start, weight, original_index)
    # Wait, no: jobs_with_indices is (end, start, weight, original_index)
    # So jobs_sorted should be a list of (start, end, weight, original_index)
    # But the original problem states jobs are (start, end, weight).
    # We need to adjust.
    # Let's restructure:
    # jobs_with_indices = [(start, end, weight, original_index) for i, (start, end, weight) in enumerate(jobs)]
    # Then sort by end, then by start, then by original_index.
    # This is the correct way.
    # Let's redo the initial sorting step to include original indices.

    # This is a major refactor. The original code did not track original indices.
    # We need to track them to map back to the original input list.
    # Let's start over with this in mind.

    # Step 1: Sort jobs by end time, then by start time, then by original index.
    # Create a list of tuples (end, start, weight, original_index)
    jobs_with_indices = []
    for original_idx, job in enumerate(jobs):
        start, end, weight = job
        jobs_with_indices.append((end, start, weight, original_idx))

    # Sort by end, then by start, then by original index
    jobs_with_indices.sort(key=lambda x: (x[0], x[1], x[3]))

    # Extract the sorted jobs and their original indices
    jobs_sorted = []
    original_indices_in_sorted = []
    for job in jobs_with_indices:
        end, start, weight, original_idx = job
        jobs_sorted.append((start, end, weight))
        original_indices_in_sorted.append(original_idx)

    n = len(jobs_sorted)
    end_times = [job[1] for job in jobs_sorted]

    # Precompute p[j] for each job j (0-based index)
    p = [0] * n
    for j in range(n):
        start_j = jobs_sorted[j][0]
        pos = bisect.bisect_right(end_times, start_j)
        p[j] = pos - 1  # -1 if no such job

    # Dynamic programming arrays
    dp = [0.0] * n
    prev = [-1] * n

    dp[0] = jobs_sorted[0][2]  # weight of first job

    for j in range(1, n):
        weight_j = jobs_sorted[j][2]
        if p[j] >= 0:
            weight_with_j = dp[p[j]] + weight_j
        else:
            weight_with_j = weight_j

        weight_without_j = dp[j-1]

        if weight_with_j > weight_without_j:
            dp[j] = weight_with_j
            prev[j] = p[j]
        else:
            dp[j] = weight_without_j
            prev[j] = j-1

    max_weight = dp[n-1]
    # Reconstruct the chosen indices in jobs_sorted
    chosen_indices_sorted = []
    current = n-1
    while current != -1:
        chosen_indices_sorted.append(current)
        current = prev[current]

    # Now, map these indices to the original input list indices
    # chosen_indices_sorted contains indices in jobs_sorted
    # original_indices_in_sorted[i] is the original index of jobs_sorted[i]
    original_chosen_indices = [original_indices_in_sorted[i] for i in chosen_indices_sorted]

    # Sort original_chosen_indices by start time, then by original index
    # We need to get the start times and original indices for these jobs
    # Create a list of tuples (start, original_index) for the chosen jobs
    chosen_with_info = []
    for idx in original_chosen_indices:
        # Find the job in the original jobs list
        # But we have original_chosen_indices, which are the original indices.
        # So for each original index, we can get the job's start time.
        # However, we need to ensure that the start times are correct.
        # Since original_chosen_indices are indices into the original jobs list,
        # we can get the start time from jobs[original_index][0]
        start = jobs[idx][0]
        chosen_with_info.append((start, idx))

    # Sort chosen_with_info by start, then by original index
    chosen_with_info.sort(key=lambda x: (x[0], x[1]))

    # Extract the original indices in the sorted order
    sorted_original_indices = [x[1] for x in chosen_with_info]

    return (max_weight, sorted_original_indices)
