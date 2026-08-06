def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Choose a subset of jobs such that no two chosen jobs overlap, maximizing the total weight.

    Args:
    jobs: A list of (start, end, weight) tuples.

    Returns:
    A tuple (total_weight, chosen_indices) where:
    - total_weight is the maximum achievable sum of weights (float);
    - chosen_indices are the indices into the input list of one optimal subset,
      sorted by the job's start time (break ties by index ascending).
    """
    # Sort jobs by end time
    jobs.sort(key=lambda x: x[1])

    # Initialize a list to store the maximum weight that can be achieved up to each job
    max_weights = [0] * len(jobs)

    # Initialize a list to store the previous job index for each job
    prev_jobs = [-1] * len(jobs)

    # Initialize the maximum weight and the index of the last chosen job
    max_weight = 0
    last_chosen = -1

    # Iterate over each job
    for i in range(len(jobs)):
        # Initialize the maximum weight that can be achieved up to the current job
        max_weight_i = 0

        # Initialize the index of the previous job for the current job
        prev_job_i = -1

        # Iterate over each previous job
        for j in range(i):
            # Check if the current job does not overlap with the previous job
            if jobs[j][1] <= jobs[i][0]:
                # Update the maximum weight that can be achieved up to the current job
                if max_weights[j] + jobs[i][2] > max_weight_i:
                    max_weight_i = max_weights[j] + jobs[i][2]
                    prev_job_i = j

        # Update the maximum weight that can be achieved up to the current job
        max_weights[i] = max_weight_i

        # Update the index of the previous job for the current job
        prev_jobs[i] = prev_job_i

        # Update the maximum weight and the index of the last chosen job
        if max_weight_i > max_weight:
            max_weight = max_weight_i
            last_chosen = i

    # Initialize a list to store the chosen job indices
    chosen_indices = []

    # Initialize the current job index
    current_job = last_chosen

    # Iterate until we reach the first job
    while current_job != -1:
        # Add the current job index to the list of chosen job indices
        chosen_indices.append(current_job)

        # Move to the previous job
        current_job = prev_jobs[current_job]

    # Return the maximum weight and the chosen job indices
    return max_weight, chosen_indices[::-1]
